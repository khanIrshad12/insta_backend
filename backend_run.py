#backend_run.py
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
def scroll_comments(driver):
    """Scroll through all comments until no more new comments are loaded"""
    print("Starting to scroll through comments...")
    
    try:
        # Wait for all instances of the class to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "x5yr21d"))
        )
        
        # Get all elements with the class and select the 10th one (index 9)
        comments_containers = driver.find_elements(By.CLASS_NAME, "x5yr21d")
        if len(comments_containers) >= 10:
            comments_container = comments_containers[9]  # Get the 10th element
            print("Found the correct comments container")
        else:
            print(f"Not enough comment containers found. Only found {len(comments_containers)}")
            return
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", comments_container)
        
        while True:
            # Scroll to bottom of comments container
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", 
                comments_container
            )
            
            # Wait for potential new comments to load
            time.sleep(random.uniform(1.5, 2.5))
            
            # Calculate new scroll height
            new_height = driver.execute_script("return arguments[0].scrollHeight", comments_container)
            
            # Break if no new comments were loaded
            if new_height == last_height:
                break
                
            last_height = new_height
            print("Scrolling for more comments...")
            
    except Exception as e:
        print(f"Error during scrolling: {e}")

def get_all_commenters(driver):
    """Get all unique commenters from the post"""
    users = set()  # Using a set to avoid duplicates
    
    try:
        # First scroll to load all comments
        scroll_comments(driver)
        
        # Wait a bit for any final loading
        time.sleep(2)
        
        # Get all comment elements
        elements = driver.find_elements(By.CLASS_NAME, "_ap3a")
        
        for element in elements:
            try:
                user_text = element.text
                if user_text and user_text != "black":
                    users.add(user_text)
            except StaleElementReferenceException:
                continue
                
        print(f"Found {len(users)} unique commenters")
        return list(users)
        
    except Exception as e:
        print(f"Error getting commenters: {e}")
        return []

def instagram_login(username, password, reelUrl, stop_event=None, driver=None):
    if driver is None:
        driver = webdriver.Chrome()
    
    try:
        # Your existing login flow
        driver.get('https://www.instagram.com/accounts/login/')
        time.sleep(5)
        
        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME,"password")

        username_input.send_keys(username)
        password_input.send_keys(password)

        login_button = driver.find_element(By.CSS_SELECTOR,"button[type='submit']")
        login_button.click()

        time.sleep(30)
        driver.get(reelUrl)

        # Check for stop event before proceeding
        if stop_event and stop_event.is_set():
            print("Automation stopped")
            return

        # Rest of your existing logic
        time.sleep(4)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_ap3a"))
        )

        # Get all commenters
        users = get_all_commenters(driver)
        print("All users found:", users)

        # Process each user's stories
        for user in users:
            # Check for stop event before processing each user
            if stop_event and stop_event.is_set():
                print("Automation stopped")
                break

            print(f"\nProcessing stories for user: {user}")
            checkStories(user, driver)
            time.sleep(random.uniform(2, 4))

    except Exception as e:
        print(f"Error in main process: {e}")
    finally:
        time.sleep(5)
        driver.quit()

def element_exists(driver, by, value):
    try:
        driver.find_element(by, value)
        return True
    except Exception as e:
        print("element not found", value)
        return False

def checkStories(username, driver):
    story_url = f"https://www.instagram.com/stories/{username}/"
    driver.get(story_url)
    time.sleep(5)

    # Check if the URL is still the story URL
    if driver.current_url != story_url:
        print(f"No stories for {username}, moving to the next user.")
        time.sleep(5)
        return  # Skip to the next user
    
    try:
        if element_exists(driver, By.CSS_SELECTOR, '[aria-label="Like"]'):
            textArea = driver.find_element(By.CSS_SELECTOR, '[aria-label="Like"]')
            textArea.click()
            print(f"Liked story directly for {username}")
            
        else:
            viewStory = driver.find_elements(By.TAG_NAME,"div")
            for ele in viewStory:
                if ele.text == "View story":
                    ele.click()

                    time.sleep(2)
                    if element_exists(driver, By.CSS_SELECTOR, '[aria-label="Like"]'):
                        storyDiv = driver.find_element(By.CLASS_NAME, "x1ned7t2")
                        noOfStories = storyDiv.find_elements(By.CLASS_NAME, "x1lix1fw")
                        
                        stories = 0
                        isActive = False
                        for j in noOfStories:
                            if element_exists(j, By.TAG_NAME, "div"):
                                isActive = True

                            if isActive:    
                                stories += 1

                        print(f'Found {stories} stories for {username}')
                        for j in range(stories):
                            
                            if element_exists(driver, By.CSS_SELECTOR, '[aria-label="Like"]'):
                                time.sleep(1)
                                actionChain = ActionChains(driver)
                               # Locate the parent div with the specified class
                                parent_div = driver.find_element(By.CSS_SELECTOR, "div[class='x6s0dn4 x78zum5 x67bb7w']")

                                # Inside this parent div, find the svg with aria-label="Like"
                                like_svg = parent_div.find_element(By.CSS_SELECTOR, "svg[aria-label='Like']")

                                # Get the grandparent element of the svg (two levels up)
                                like_button = like_svg.find_element(By.XPATH, "./../../..")
                                actionChain.move_to_element(like_button).perform()
                                print(like_button.get_attribute("outerHTML"))
                                # Click the like button
                                like_button.click()
                               
                                print(f"Liked story {j+1} for {username}")
                                time.sleep(4)
                                
                                if element_exists(driver, By.CSS_SELECTOR, '[aria-label="Next"]'):
                                    next_button_svg = driver.find_element(By.CSS_SELECTOR, '[aria-label="Next"]')
                                    next_button_svg.click()
                                    print("Moved to next story")

                                #time.sleep(3)
                    break
        time.sleep(5)
    except Exception as e:
        print(f"Error processing stories for {username}: {e}")
        print("error\n")

# Add function to debug class positions
def debug_class_positions(driver):
    """Print out all instances of x5yr21d class for debugging"""
    elements = driver.find_elements(By.CLASS_NAME, "x5yr21d")
    print(f"\nFound {len(elements)} instances of x5yr21d class")
    for i, element in enumerate(elements):
        try:
            # Try to get some identifying information about each instance
            parent_class = element.find_element(By.XPATH, "..").get_attribute("class")
            print(f"Element {i}: Parent class: {parent_class}")
        except:
            print(f"Element {i}: Could not get parent info")

""" instagram_login("devilboy_37","@#$_&-+()/","https://www.instagram.com/p/Cz47qS1oZiW/") """