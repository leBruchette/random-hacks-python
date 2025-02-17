from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import os
import time

service = Service('/opt/homebrew/bin/chromedriver')
driver = webdriver.Chrome(service=service)


# Open the URL
with open('events.txt', 'r') as file:
    for event_year_and_id in file:
        print(F'processing {event_year_and_id}')
        event_permit = event_year_and_id.replace("/results/index.php?year=", "").replace("&id=", "-")
        url = f'https://legacy.usacycling.org/results/index.php?permit={event_permit}'
        driver.get(url)
        # Give the page time to load
        time.sleep(3)

        # Create a directory to store the results for permit id
        event_dir = f'./data/events/{event_permit}'
        os.makedirs(event_dir, exist_ok=True)

        # Find anchor tags with href containing javascript:void(0)
        anchor_tags = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"]')
        onclick_properties = []

        # Find anchor tags with onclick starting with loadInfoID
        # These are the sub-events that we'll need to click to get the results, will require reloading `url`
        for anchor in anchor_tags:
            onclick_property = anchor.get_attribute('onclick')
            if onclick_property is not None and onclick_property.startswith('loadInfoID'):
                onclick_properties.append(onclick_property)

        # there will not be any sub-events if the onclick_properties list is empty...i.e. single event permit
        for onclick_value in onclick_properties:
            # reload the page to move to the next sub-event
            driver.get(url)
            try:
                subevent_id = onclick_value.split('loadInfoID(')[1].split(',')[0]
                with open(os.path.join(event_dir, f'{subevent_id}.txt'), 'a') as file:
                    file.write(f'-----\n{onclick_value.split("'")[1]}\n')

                sub_event_anchor = driver.find_element(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="{onclick}"]'.format(onclick=onclick_value))
                # Click to load the sub-event
                sub_event_anchor.click()
                time.sleep(1)  # Give time for content to load
            except Exception as e:
                print(f'Could not load sub-event from url: {e}')

            # Find anchor tags that expand the results for a category of an event
            category_anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"]')
            for category in category_anchors:
                try:
                    # ignore 'Feedback' which opens a modal
                    if category.text == 'Feedback':
                        continue
                    category.click()
                    time.sleep(3)  # Give time for content to load
                    with open(os.path.join(event_dir, f'{subevent_id}.txt'), 'a') as file:
                        file.write(f'---\nCategory: {category.text}\n')

                    # print(f'---\nCategory: {category.text}\n')
                except Exception as e:
                    print(f'Could not toggle category div: {e}')

                # Find anchor tags with href containing ?compId=
                # the text of these anchors are license numbers we'd like to collect
                usac_anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href*="?compid="]')
                for usac_anchor in usac_anchors:
                    try:
                        if usac_anchor.text == '':
                            continue
                        with open(os.path.join(event_dir, f'{subevent_id}.txt'), 'a') as file:
                            file.write(f'usac_id: {usac_anchor.text}\n')

                        # print("usac_id: " + usac_anchor.text)
                    except Exception as e:
                        print(f'Could not scrape license from anchor: {e}')
        print(f'Finished processing {event_year_and_id}')
    # Close the browser
driver.quit()
