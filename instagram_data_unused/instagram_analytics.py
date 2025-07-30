#!/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json, time, os, re
import sqlite3
import threading
import schedule
import logging



# List of users
users = ['bidukbidukberlabuh']



# ----------------------------------------
#  InstAnalytics function
# ----------------------------------------

def InstAnalytics(browser):
	print("Starting analytics function...")
	# This will hold all user data for this run
	all_users_data = []

	for user in users:
		print(f"\nScraping data for user: {user}")
		
		# User's profile
		url = 'https://instagram.com/' + user
		print(f"Opening profile: {url}")
		browser.get(url)
		time.sleep(5) # Increased sleep time for page load

		# Soup
		soup = BeautifulSoup(browser.page_source, 'html.parser')
		print("Page source parsed.")

		# User's statistics
		try:
			# Instagram's classes often change. This is a potential point of failure.
			# Using a more generic selector based on shared text content.
			spans = soup.find_all('span', class_=lambda x: x and x.startswith('_ac2a'))
			
			if len(spans) < 3:
				print("Could not find user statistics elements using primary selector. Trying fallback.")
				# Fallback based on order if classes fail
				stats_list = soup.select('header section ul li')
				if len(stats_list) < 3:
					raise ValueError("Could not find stats elements.")
				postsT = stats_list[0].get_text().split(' ')[0]
				followersT = stats_list[1].get_text().split(' ')[0]
				followingT = stats_list[2].get_text().split(' ')[0]
			else:
				postsT     = spans[0].get_text()
				followersT = spans[1].get_text()
				followingT = spans[2].get_text()

			print(f"Raw stats: Posts - {postsT}, Followers - {followersT}, Following - {followingT}")
		except Exception as e:
			print(f"Error scraping user statistics: {e}")
			print("Page content saved to debug.html")
			with open('debug.html', 'w', encoding='utf-8') as f:
				f.write(browser.page_source)
			continue


		# Remove all non-numeric characters
		posts     = int(re.sub('[^0-9]', '', postsT))
		followers = int(re.sub('[^0-9]', '', followersT))
		following = int(re.sub('[^0-9]', '', followingT))

		# Convert k to thousands and m to millions
		if 'k' in postsT.lower(): posts = int(float(postsT.replace('k','').replace(',','.'))*1000)
		if 'k' in followersT.lower(): followers = int(float(followersT.replace('k','').replace(',','.'))*1000)
		if 'k' in followingT.lower(): following = int(float(followingT.replace('k','').replace(',','.'))*1000)
		if 'm' in postsT.lower(): posts = int(float(postsT.replace('m','').replace(',','.'))*1000000)
		if 'm' in followersT.lower(): followers = int(float(followersT.replace('m','').replace(',','.'))*1000000)
		if 'm' in followingT.lower(): following = int(float(followingT.replace('m','').replace(',','.'))*1000000)
		print(f"Cleaned stats: Posts - {posts}, Followers - {followers}, Following - {following}")


		# Scrolling is necessary to load all posts
		print("Scrolling to load posts...")
		last_height = browser.execute_script("return document.body.scrollHeight")
		
		# Scroll down to load all posts based on the known post count
		scroll_count = 0
		# We know how many posts there should be in total from the profile header
		# Instagram typically shows 12 posts initially, then loads 12 more with each scroll
		expected_scrolls = max(1, (posts - 12) // 12 + 1)  # Calculate expected number of scrolls needed
		
		print(f"Total posts: {posts}, expected scrolls needed: {expected_scrolls}")
		
		max_scrolls = expected_scrolls + 15  # Add a larger buffer to ensure we load everything
		stagnant_count = 0  # Counter for when scrolling doesn't load new content
		consecutive_same_count = 0  # For more accurate detection of end of scrolling
		previous_post_count = 0  # Track post count to determine if more posts were loaded
		
		print(f"Starting aggressive scrolling to load all {posts} posts (max {max_scrolls} scrolls)...")
		while scroll_count < max_scrolls:
			# Scroll down
			browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			time.sleep(3)  # Give more time for content to load
			
			# Sometimes we need to click "Load more" buttons if they appear
			try:
				load_more_buttons = browser.find_elements(By.XPATH, 
					"//button[contains(text(), 'Load more') or contains(text(), 'Show more') or contains(text(), 'See more')]")
				if load_more_buttons:
					load_more_buttons[0].click()
					print("Clicked 'Load more' button")
					time.sleep(3)  # Wait for new content
			except Exception as e:
				print(f"No 'Load more' button found or error clicking it: {e}")
			
			# Get new height and check post count
			new_height = browser.execute_script("return document.body.scrollHeight")
			
			# Check post count using multiple methods to be thorough
			post_links_xpath = browser.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
			post_links_js = browser.execute_script("""
				return Array.from(document.querySelectorAll('a[href*="/p/"]')).map(a => a.href);
			""")
			
			# Combine and deduplicate post links
			all_post_hrefs = []
			all_post_hrefs.extend([elem.get_attribute('href') for elem in post_links_xpath if elem.get_attribute('href')])
			all_post_hrefs.extend(post_links_js)
			unique_post_hrefs = set(all_post_hrefs)
			current_post_count = len(unique_post_hrefs)
			
			print(f"Currently loaded {current_post_count}/{posts} unique posts (scroll {scroll_count+1}/{max_scrolls})")
			
			# If we have all posts, we can stop
			if current_post_count >= posts:
				print(f"Successfully loaded all {posts} posts. Stopping scrolling.")
				break
				
			# Check if we're making progress
			if current_post_count > previous_post_count:
				print(f"Progress: +{current_post_count - previous_post_count} new posts found")
				consecutive_same_count = 0
			else:
				consecutive_same_count += 1
				print(f"No new posts found after scroll {scroll_count+1} (consecutive: {consecutive_same_count}/5)")
				
				# If we've scrolled 5 times and post count hasn't increased, try more aggressive tactics
				if consecutive_same_count >= 5:
					print("Post count not increasing. Trying random scrolls to trigger lazy loading...")
					
					# Try scrolling up and down a bit to trigger lazy loading
					for _ in range(3):
						# Scroll up partially
						browser.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
						time.sleep(1)
						# Scroll down again
						browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
						time.sleep(2)
					
					# If still no progress after aggressive tactics
					if consecutive_same_count >= 8:
						print("Reached the limit of scrolling effectiveness. Some posts may be unavailable.")
						break
			
			# Also check if height is stagnant (different approach)
			if new_height == last_height:
				stagnant_count += 1
				print(f"No new content height after scroll {scroll_count+1} (stagnant: {stagnant_count}/3)")
				if stagnant_count >= 3:
					print("Page height not increasing. Using JavaScript to find remaining posts...")
					
					# Try to force-load missing posts using JavaScript
					try:
						browser.execute_script("""
							// Try to find all post containers and ensure they're loaded
							var postContainers = document.querySelectorAll('article a');
							for (var i = 0; i < postContainers.length; i++) {
								// Attempt to scroll each container into view
								postContainers[i].scrollIntoView();
							}
						""")
						time.sleep(3)  # Wait for potential new loads
					except:
						print("JavaScript post loading attempt failed")
					
					if stagnant_count >= 5:
						print("Maximum stagnation reached - page may not have all posts loaded")
						break
			else:
				stagnant_count = 0  # Reset if height changes
			
			# Update for next iteration
			previous_post_count = current_post_count
			last_height = new_height
			scroll_count += 1
		
		print(f"Completed {scroll_count} scrolls. Ready to collect post data.")
		
		# Find post links using multiple approaches for maximum coverage
		print("Finding post links from profile using multiple methods...")
		links = []
		
		# Method 1: Execute JavaScript to get all post links (most reliable)
		print("Method 1: Using JavaScript DOM query...")
		js_links = browser.execute_script("""
			const links = [];
			// Get all anchor tags with /p/ in href
			const anchors = document.querySelectorAll('a[href*="/p/"]');
			for (let i = 0; i < anchors.length; i++) {
				links.push(anchors[i].href);
			}
			return links;
		""")
		
		initial_js_count = len(js_links)
		print(f"JavaScript found {initial_js_count} links")
		
		# Add links found via JavaScript
		for href in js_links:
			if href and '/p/' in href and href not in links:
				links.append(href)
		
		# Method 2: Use traditional Selenium XPath method
		print("Method 2: Using Selenium XPath...")
		post_elements = browser.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
		selenium_count = len(post_elements)
		print(f"Selenium XPath found {selenium_count} elements")
		
		for elem in post_elements:
			href = elem.get_attribute('href')
			if href and '/p/' in href and href not in links:
				links.append(href)
				
		# Method 3: CSS Selector approach
		print("Method 3: Using CSS Selectors...")
		css_elements = browser.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
		css_count = len(css_elements)
		print(f"CSS Selector found {css_count} elements")
		
		for elem in css_elements:
			href = elem.get_attribute('href')
			if href and '/p/' in href and href not in links:
				links.append(href)
		
		print(f"Found {len(links)} unique photo links combined from all methods")
		
		# Debug comparison of methods
		print(f"Method comparison - JavaScript: {initial_js_count}, XPath: {selenium_count}, CSS: {css_count}, Combined unique: {len(links)}")

		if not links:
			# Try direct interaction with the grid
			print("No links found with standard methods. Trying grid interaction approach...")
			try:
				# Try multiple selectors to find the post grid
				grid_selectors = [
					'//article[contains(@class, "x1iyjqo2")]//div[contains(@style, "grid")]',
					'//article//div[contains(@style, "grid")]',
					'//div[contains(@class, "_aagw")]',  # Instagram post grid class
					'//article//div[contains(@class, "grid")]',
					'//main//article',  # Most generic article container
				]
				
				for selector in grid_selectors:
					try:
						print(f"Trying grid selector: {selector}")
						grid = browser.find_element(By.XPATH, selector)
						posts = grid.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
						if not posts:
							posts = grid.find_elements(By.XPATH, './/a[contains(@href, "/p/")]')
						if posts:
							print(f"Found {len(posts)} posts using selector: {selector}")
							break
					except Exception:
						print(f"Selector {selector} did not find elements")
						posts = []
						continue
				
				# Try to get links from these posts
				for post in posts:
					try:
						href = post.get_attribute('href')
						if href and '/p/' in href and href not in links:
							links.append(href)
					except Exception as e:
						print(f"Error getting link from post: {e}")
				
				print(f"Added {len(links)} links from direct grid interaction")
			except Exception as e:
				print(f"Grid interaction failed: {e}")
		
		# Now, let's try a completely different approach if we still have no links
		if not links:
			print("Still no links found. Trying direct search for all 'a' tags with '/p/' in href...")
			
			# Try to find all a tags with /p/ in href directly
			try:
				post_links = browser.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
				print(f"Found {len(post_links)} potential post links")
				
				for link_element in post_links:
					try:
						href = link_element.get_attribute('href')
						if href and href not in links:
							links.append(href)
							print(f"Added link: {href}")
					except Exception as e:
						print(f"Error extracting link: {e}")
			except Exception as e:
				print(f"Direct link search failed: {e}")

		photosDic = []
		pLikesT = 0
		pCounter = 0
		
		print(f"Final link count: {len(links)}")
		
		# Process all unique links
		unique_links = list(set(links))  # Remove duplicates
		print(f"Found {len(unique_links)} unique post links")
		
		# Check if we have all posts that we expect
		if len(unique_links) < posts:
			print(f"WARNING: Only found {len(unique_links)} unique links but profile shows {posts} posts")
			print("Attempting one final effort to find missing posts...")
			
			# Try direct JavaScript approach to find ALL post links
			try:
				browser.get(url)  # Go back to profile page
				time.sleep(3)
				
				# Execute more aggressive JavaScript to find posts
				js_links_aggressive = browser.execute_script("""
					// Allow time for dynamic content to load
					setTimeout(function() {}, 2000);
					
					// Scroll a few times
					for (let i = 0; i < 5; i++) {
						window.scrollTo(0, document.body.scrollHeight);
						setTimeout(function() {}, 1000);
					}
					
					// Find all post links with multiple approaches
					const links = new Set();
					
					// Standard approach
					document.querySelectorAll('a[href*="/p/"]').forEach(a => links.add(a.href));
					
					// Find image containers that might be posts
					document.querySelectorAll('article img').forEach(img => {
						let parent = img;
						// Go up the DOM to find the closest anchor
						for (let i = 0; i < 5; i++) {
							parent = parent.parentElement;
							if (!parent) break;
							
							if (parent.tagName === 'A' && parent.href && parent.href.includes('/p/')) {
								links.add(parent.href);
								break;
							}
						}
					});
					
					return Array.from(links);
				""")
				
				# Add new links found
				for href in js_links_aggressive:
					if href and '/p/' in href and href not in unique_links:
						unique_links.append(href)
				
				print(f"After aggressive JavaScript search: found {len(unique_links)} unique links")
			except Exception as e:
				print(f"Aggressive JavaScript approach failed: {e}")
		
		# Final check on our links
		if len(unique_links) < posts:
			print(f"NOTICE: Could only find {len(unique_links)}/{posts} posts. Some posts may be private or unavailable.")
		
		# Process all posts, aim to process as many as we know exist
		max_posts = min(len(unique_links), posts)
		print(f"Will process {max_posts} posts out of {posts} total posts ({len(unique_links)} unique links found)")
		
		for i in range(max_posts):
			link = unique_links[i]
			try:
				# Photo Id - extract from URL 
				# Handle both full URLs and relative paths
				if '/p/' in link:
					pId = link.split('/p/')[1].split('/')[0]
				else:
					pId = link.split('/')[-1]
					
				print(f"Processing photo {i + 1}/{max_posts}, ID: {pId}")
				
				# Navigate to the post URL
				browser.get(link)
				time.sleep(3)  # Wait for page to load
				
				# Find likes using various methods
				pLikes = 0
				try:
					# Look for elements that might contain like counts
					like_elements = browser.find_elements(By.XPATH, 
						"//section//div[contains(text(), ' likes') or contains(text(), ' like') or contains(text(), ' views')]|" +
						"//section//span[contains(text(), ' likes') or contains(text(), ' like') or contains(text(), ' views')]"
					)
					
					if like_elements:
						likes_text = like_elements[0].text
						print(f"Found likes text: {likes_text}")
						pLikes = int(re.sub('[^0-9]', '', likes_text)) if likes_text else 0
					else:
						print("Could not find likes text through primary method")
						
						# Try an alternative approach - look for aria-label attributes
						aria_elements = browser.find_elements(By.XPATH, "//*[contains(@aria-label, 'like') or contains(@aria-label, 'Like')]")
						if aria_elements:
							for elem in aria_elements:
								aria_text = elem.get_attribute('aria-label')
								print(f"Found aria-label: {aria_text}")
								if aria_text and re.search(r'\d+', aria_text):
									pLikes = int(re.sub('[^0-9]', '', aria_text))
									break
				except Exception as e:
					print(f"Error finding likes: {e}")
					pLikes = 0
				
				# Count comments - look for comment indicators
				pComments = 0
				try:
					# Find comment section or comment count elements
					comment_elements = browser.find_elements(By.XPATH, 
						"//span[contains(text(), ' comments') or contains(text(), ' comment')]|" +
						"//div[contains(text(), ' comments') or contains(text(), ' comment')]"
					)
					
					if comment_elements:
						comments_text = comment_elements[0].text
						print(f"Found comments text: {comments_text}")
						pComments = int(re.sub('[^0-9]', '', comments_text)) if comments_text else 0
					else:
						# Alternative: count visible comments
						comments = browser.find_elements(By.XPATH, "//ul//li[.//div[@role='button']]")
						pComments = len(comments)
						print(f"Counted {pComments} visible comments")
				except Exception as e:
					print(f"Error counting comments: {e}")
					pComments = 0

				# Photo dictionary
				photoDic = {
					'pId': pId,
					'pLikes': pLikes,
					'pComments': pComments
				}
				photosDic.append(photoDic)
				# Total likes
				pLikesT += pLikes
				# Simple counter
				pCounter += 1
			except Exception as e:
				print(f"Could not process photo link {link}. Error: {e}")
				continue


		# Dictionary
		userDic = {
			'username': user,
			'date': datetime.now().strftime("%Y-%m-%d"),
			'data': {
				'posts': posts,
				'followers': followers,
				'following': following,
				'pLikesT': pLikesT,
				'photos': photosDic
			}
		}

		# Add the completed user dictionary to our list for this run
		all_users_data.append(userDic)
		print(f"Successfully scraped data for {user}.")
		
	# After processing all users, save data to a JSON file and SQLite database
	print("\nSaving data to JSON and SQLite database...")
	try:
		# Save data to JSON file
		with open('InstAnalytics.json', 'w') as iaFile:
			json.dump(all_users_data, iaFile, indent=4)
		
		print("Data successfully saved to InstAnalytics.json")
		
		# Save data to SQLite database
		save_to_sqlite(all_users_data)
		
		print("Data successfully saved to SQLite database")
	
	except Exception as e:
		print(f"Error saving data: {e}")

# ----------------------------------------
#  SQLite Database Functions
# ----------------------------------------

def init_database():
	"""Initialize SQLite database with required tables"""
	conn = sqlite3.connect('instagram_analytics.db')
	cursor = conn.cursor()
	
	# Create user_stats table to store user statistics
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS user_stats (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT,
			date TEXT,
			timestamp TEXT,
			posts INTEGER,
			followers INTEGER,
			following INTEGER,
			total_likes INTEGER
		)
	''')
	
	# Create post_stats table to store individual post data
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS post_stats (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT,
			post_id TEXT,
			date TEXT,
			timestamp TEXT,
			likes INTEGER,
			comments INTEGER
		)
	''')
	
	conn.commit()
	conn.close()
	print("Database initialized successfully")


def save_to_sqlite(user_data_list):
	"""Save scraped data to SQLite database"""
	conn = sqlite3.connect('instagram_analytics.db')
	cursor = conn.cursor()
	
	current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	for user_data in user_data_list:
		username = user_data['username']
		date = user_data['date']
		
		# Extract main statistics
		posts = user_data['data']['posts']
		followers = user_data['data']['followers'] 
		following = user_data['data']['following']
		total_likes = user_data['data']['pLikesT']
		
		# Insert into user_stats table
		cursor.execute('''
			INSERT INTO user_stats (username, date, timestamp, posts, followers, following, total_likes) 
			VALUES (?, ?, ?, ?, ?, ?, ?)
		''', (username, date, current_timestamp, posts, followers, following, total_likes))
		
		# Insert individual post data
		for post in user_data['data']['photos']:
			post_id = post['pId']
			likes = post['pLikes']
			comments = post['pComments']
			
			cursor.execute('''
				INSERT INTO post_stats (username, post_id, date, timestamp, likes, comments)
				VALUES (?, ?, ?, ?, ?, ?)
			''', (username, post_id, date, current_timestamp, likes, comments))
	
	conn.commit()
	conn.close()
	print(f"Data for {len(user_data_list)} users saved to SQLite database")


# ----------------------------------------
#  Scheduler Functions
# ----------------------------------------

def setup_logger():
	"""Set up logging for scheduled tasks"""
	logging.basicConfig(
		filename='instagram_analytics.log',
		level=logging.INFO,
		format='%(asctime)s - %(levelname)s - %(message)s'
	)
	return logging.getLogger('instagram_analytics')

logger = setup_logger()

def scheduled_task():
	"""Task to be run on schedule"""
	logger.info("Starting scheduled Instagram analytics task")
	try:
		# Initialize browser
		options = webdriver.ChromeOptions()
		options.add_argument('--headless')  # Run in headless mode for scheduled tasks
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument("window-size=1200x600")
		options.add_argument("--disable-blink-features=AutomationControlled")
		options.add_experimental_option("excludeSwitches", ["enable-automation"])
		options.add_experimental_option("useAutomationExtension", False)
		options.add_argument("user-data-dir=chrome_profile")
		
		browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
		browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
			"source": """
			Object.defineProperty(navigator, 'webdriver', {
				get: () => undefined
			})
			"""
		})
		
		logger.info("Browser initialized")
		
		# Run the analytics function
		InstAnalytics(browser)
		
		logger.info("Instagram analytics completed successfully")
	except Exception as e:
		logger.error(f"Error in scheduled task: {e}")
	finally:
		try:
			browser.quit()
			logger.info("Browser closed")
		except:
			pass


def run_scheduler():
	"""Run the scheduler to execute tasks at regular intervals"""
	schedule.every(1).hour.do(scheduled_task)
	logger.info("Scheduler initialized - tasks will run every hour")
	
	while True:
		schedule.run_pending()
		time.sleep(60)  # Check every minute


# ----------------------------------------
#  Main
# ----------------------------------------

if __name__ == '__main__':
	print("Instagram Analytics Tool")
	# Initialize the database
	init_database()
	
	# Parse command line arguments
	import argparse
	parser = argparse.ArgumentParser(description='Instagram Analytics Tool')
	parser.add_argument('--schedule', action='store_true', help='Run in scheduled mode (every hour)')
	parser.add_argument('--now', action='store_true', help='Run once immediately')
	args = parser.parse_args()
	
	if args.schedule:
		print("Running in scheduled mode - will collect data every hour")
		print("Press Ctrl+C to stop")
		# Run the scheduled task once immediately
		scheduled_task()
		# Start the scheduler in a separate thread
		scheduler_thread = threading.Thread(target=run_scheduler)
		scheduler_thread.daemon = True
		scheduler_thread.start()
		
		# Keep the main thread alive to allow Ctrl+C to work
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			print("Scheduler stopped by user")
			exit()
	elif args.now:
		print("Running analytics once...")
		scheduled_task()
		print("Task completed")
	else:
		# Default behavior - run once with visual browser
		print("Initializing browser with persistent session...")
	# Launch browser
	options = webdriver.ChromeOptions()
	# options.add_argument('--headless') # Keep disabled for debugging
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument("window-size=1200x600")
	# Some additional options to make scraping more reliable
	options.add_argument("--disable-blink-features=AutomationControlled")
	options.add_experimental_option("excludeSwitches", ["enable-automation"])
	options.add_experimental_option("useAutomationExtension", False)
	# Add this line to save your session
	options.add_argument("user-data-dir=chrome_profile")
	browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
	# Mask the webdriver to avoid detection
	browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
		"source": """
		Object.defineProperty(navigator, 'webdriver', {
			get: () => undefined
		})
		"""
	})
	print("Browser initialized.")

	try:
		print("Checking login status...")
		browser.get('https://www.instagram.com/')
		time.sleep(5) # Wait for page to load and redirect if necessary

		# Check if we need to log in by looking for the username field
		# Use find_elements to avoid an exception if it's not found
		username_field = browser.find_elements(By.NAME, 'username')

		if username_field:
			print("Login required. Attempting to log in...")
			username = os.environ.get('INSTAGRAM_USERNAME')
			password = os.environ.get('INSTAGRAM_PASSWORD')

			if not username or not password:
				print("Error: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables are not set.")
				browser.quit()
				exit()
			
			username_input = username_field[0]
			password_input = browser.find_element(By.NAME, 'password')
			
			print("Entering credentials...")
			username_input.send_keys(username)
			password_input.send_keys(password)
			
			print("Submitting login form...")
			password_input.send_keys(Keys.RETURN)
			
			print("Waiting for login to complete...")
			WebDriverWait(browser, 20).until(
				EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Save Your Login Info')] | //*[contains(text(), 'Not Now')] | //a[contains(@href, '/{}/')]".format(username)))
			)
			print("Login successful! Session is saved.")
		else:
			print("Already logged in. Skipping login process.")

	except Exception as e:
		print(f"An error occurred during login check/attempt: {e}")
		print("Saving screenshot to login_error.png")
		browser.save_screenshot('login_error.png')
		browser.quit()
		exit()


	# Create empty JSON file if it doesn't exist
	if not os.path.isfile('InstAnalytics.json'):
		print("Creating new InstAnalytics.json file")
		with open('InstAnalytics.json', 'w') as iaFile:
			json.dump([], iaFile, indent=4)

	print('Starting Instagram analytics script for testing...')
	try:
		InstAnalytics(browser)
		print("\nScript finished successfully.")
	except Exception as e:
		print(f"\nAn unexpected error occurred: {e}")
	finally:
		# Quit browser
		browser.quit()
		print("\nBrowser closed.")