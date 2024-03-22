from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.common import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import mysql.connector

# Establish a connection to the MySQL server
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="JobPosting"
)

# Create a cursor object to execute SQL queries
cursor = mydb.cursor()

# Define the SQL query to create the JobPositions table
create_table_query = """
CREATE TABLE IF NOT EXISTS Jobs (
    Job_id INT AUTO_INCREMENT PRIMARY KEY,
    Company VARCHAR(255),
    Position VARCHAR(255),
    Skills VARCHAR(255),
    Rating VARCHAR(255),
    Seniority VARCHAR(255),
    Place VARCHAR(255)
)
"""

# Execute the SQL query to create the table
cursor.execute(create_table_query)

# Commit the changes to the database
mydb.commit()

# Open tab in incognito mode in order to avoid previous data being loaded, such as
# cookies, site data or information entered in forms saved on the device.
options = Options()
options.add_argument("--incognito")

# Setting experimental option 'detach' to True in order to window stay open.
options.add_experimental_option('detach', True)

# Get the web driver path for Homepage.
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()
url = 'https://www.helloworld.rs/oglasi-za-posao/?isource=Helloworld.rs&icampaign=home-fancy-intro&imedium=site'
driver.get(url)

time.sleep(2)

# Click the button to show jobs related to programming, or comment this statement to scrape all job offers.
# driver.find_element(By.XPATH, '//*[@data-tag-id="281"]').click()
# time.sleep(1)

# Set flag to control the flow of execution.
flag = True

# The script will continue execution as long as the flag remains set to True.
while flag:
    # Get the page source.
    page_source = driver.page_source

    # Parse the HTML content.
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find element which contains all job offers on page.
    job_offers = soup.find('div', class_='mx-auto px-4 py-8')

    # Find all job offers on the page.
    jobs = job_offers.find_all('div', class_='relative', attrs={"class": "relative z-1 flex flex-col"})

    # Remove words that will mess up data.
    words_to_remove = ["Premium", "Novo", "konkuriši", "među", "prvima"]

    skill_list = []

    # Find elements with specific number of parents
    for job in jobs:
        num_parents = len(list(job.parents))
        if num_parents >= 8:
            continue
        # Find company name
        company = job.find("h4", class_="font-semibold").text.strip()

        # Find name of the position
        position = job.find("h3").text.strip()

        # Find town or country for the position or remote if it is
        place = job.find("p", class_="font-semibold")
        if place:
            place_text = place.text.strip()
        else:
            place_text = None

        # Find rating if company have any.
        rating_stars = job.find("span", class_="inline-block")
        if rating_stars is not None:
            rating = rating_stars.text.strip()
        else:
            rating = None

        # Find skills for the position.
        skills = job.find_all("a", class_="btn-xs")
        for skill in skills:
            skill_list.append(skill.text.strip())
        if not skill_list:
            skill_list = None

        # Find seniority
        seniority = job.find("button", class_="btn").text.strip()

        # Clear out words that are unnecessary
        if any(word in text for text in [company, position, skills] for word in words_to_remove):
            continue

        # If list is empty return None to avoid error
        if skill_list is None:
            joined_skills = None
        else:
            joined_skills = ', '.join(skill_list)

        # Insert data into the Jobs table
        insert_query = """
            INSERT INTO Jobs (Company, Position, Skills, Rating, Seniority, Place)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

        # Insert scraped data into database
        data = (company, position, joined_skills, rating, seniority, place_text)

        # Execute the insert query
        cursor.execute(insert_query, data)

        # Commit the changes to the database
        mydb.commit()

        # Empty list after collecting all skills and prepare it for next iteration.
        skill_list = []

    # Click next button, to load new page and if next_button can not be found set flag to False to end script correctly.
    time.sleep(2)
    try:
        next_button = driver.find_element(By.CLASS_NAME, "la-angle-right")
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(2)
    except NoSuchElementException:
        flag = False

# Close the cursor.
cursor.close()

# Close the database connection.
mydb.close()

# Quit the WebDriver instance to close the browser.
driver.quit()
