from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import json
import os

# constants
SET_LIST_SEPARATOR = "; "

# main class
class Main():
    def __init__(self, word_count=3, meaning_count=4):

        # settings
        self.word_count = word_count
        self.meaning_count = meaning_count

        # creating driver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

        # main properties
        self.kanji = []
        self.kanji_set = {}

        # scanning input
        self.scan_input()
        self.generate_json()

    def prompt_generate_quiz(self, kanji_data, file_name):
        global SET_LIST_SEPARATOR

        # checking answer
        answer = input("\nWould you also like to generate a .set file for this kanji set? Answer 'yes' if yes, and anything else if no.\n")
        if answer.lower() != "yes":
            return
        
        # getting ready to create quiz data
        try:
            os.makedirs("output/set")
        except:
            pass
        quiz_string = ""

        # looping through all kanji
        for kanji in kanji_data:
            data = kanji_data[kanji]
            
            # adding readings and meanings
            kunyomi = SET_LIST_SEPARATOR.join(data["kunyomi"])
            onyomi = SET_LIST_SEPARATOR.join(data["onyomi"])
            meanings = SET_LIST_SEPARATOR.join(data["meanings"])

            if len(data["kunyomi"]) > 0:
                quiz_string += f"{kanji}（訓読み）,{kunyomi}\n"
            if len(data["onyomi"]) > 0:
                quiz_string += f"{kanji}（音読み）,{onyomi}\n"
            quiz_string += f"{kanji}（いみ）,{meanings}\n"

            # adding words and word meanings
            for word_data in data["words"]:
                word_meanings = SET_LIST_SEPARATOR.join(word_data["meanings"])

                quiz_string += f"{word_data["word"]}（ふりがな）,{word_data["furigana"]}\n"
                quiz_string += f"{word_data["word"]}（いみ）,{word_meanings}\n"

        # creating file
        with open(f"output/set/{file_name}.set", "w", encoding="utf-8") as f:
            f.write(quiz_string)

        # output
        print("Completed generating .set file for kanji data.")

    def generate_json(self):
        global CSV_LIST_SEPARATOR

        # gathering data
        kanji_data = self.get_kanji_data()
        json_string = json.dumps(kanji_data)
        
        # asking for file name
        file_name = input("\nWhat would you like to name the resultant .json file with the kanji data?\n")

        # generating .json file
        try:
            os.makedirs("output/json")
        except:
            pass

        with open(f"output/json/{file_name}.json", "w", encoding="utf-8") as f:
            f.write(json_string)

        print("Successfully created .json file for kanji data output. It can be found in the \"output\" folder.")

        # prompting to generate quiz
        self.prompt_generate_quiz(kanji_data, file_name)
        
    def get_kanji_data(self):
        print("Gathering kanji data . . . ")

        # navigating to jisho
        self.driver.get("https://jisho.org")
        
        # looping and searching all kanji
        kanji_data = {}
        for kanji in self.kanji_set:
            kunyomi, onyomi, meanings, words = self.search_kanji(kanji)
            kanji_data[kanji] = {
                "kunyomi" : kunyomi,
                "onyomi" : onyomi,
                "meanings" : meanings,
                "words" : words
            }

            # printing progress
            percentage = len(kanji_data.keys()) / len(self.kanji_set)
            print(f"Completed {kanji}, {round(percentage * 100)}% progressed")

        # returning
        print("Finished gathering kanji data.")
        self.driver.quit()
        return kanji_data

    def search_kanji(self, kanji: str):

        # searching kanji
        search_bar = self.driver.find_element(by=By.ID, value="keyword")
        search_bar.click()
        search_bar.clear()
        search_bar.send_keys(kanji + " #kanji")

        search_button = self.driver.find_element(by=By.CSS_SELECTOR, value=".submit .icon")
        search_button.click()

        # finding reading containers
        kunyomi_container = None
        onyomi_container = None
        try: 
            kunyomi_container = self.driver.find_element(by=By.CSS_SELECTOR, value=".kanji-details__main-readings>.dictionary_entry.kun_yomi")
        except:
            pass
        try:
            onyomi_container = self.driver.find_element(by=By.CSS_SELECTOR, value=".kanji-details__main-readings>.dictionary_entry.on_yomi")
        except:
            pass
        
        # finding readings
        all_kunyomi = []
        all_onyomi = []

        if kunyomi_container != None:
            kunyomi_elements = kunyomi_container.find_elements(by=By.TAG_NAME, value="a")
            for element in kunyomi_elements:
                all_kunyomi.append(element.text)

        if onyomi_container != None:
            onyomi_elements = onyomi_container.find_elements(by=By.CSS_SELECTOR, value="a")
            for element in onyomi_elements:
                all_onyomi.append(element.text)

        # finding meanings
        meanings_container = self.driver.find_element(by=By.CSS_SELECTOR, value=".kanji-details__main-meanings")
        meanings = meanings_container.text.replace(" ", "").split(",")[0:self.meaning_count]

        # clicking words button
        link_buttons = self.driver.find_elements(by=By.CSS_SELECTOR, value=".small-12.large-10.columns>.inline-list>li>a")
        words_button = None

        for button in link_buttons:
            if button.text.startswith("Words containing"):
                words_button = button
                break

        words_button.click()

        # finding first few words
        words = []
        word_containers = self.driver.find_elements(by=By.CSS_SELECTOR, value="#primary>.concepts>.concept_light.clearfix")

        for i, container in enumerate(word_containers):
            if len(words) >= self.word_count:
                break

            # finding word and reading
            word = container.find_element(by=By.CSS_SELECTOR, value="span.text").text
            furigana_container = container.find_element(by=By.CSS_SELECTOR, value="span.furigana")
            if not kanji in word:
                continue

            # adding non-kanji parts of word to furigana
            furigana_elements = furigana_container.find_elements(by=By.CSS_SELECTOR, value="span")
            furigana = ""
            for i, char in enumerate(word):
                if len(furigana_elements) > i and furigana_elements[i].text != "":
                    furigana += furigana_elements[i].text
                else:
                    furigana += char

            # finding meanings
            word_meanings = []
            meanings_container = container.find_element(by=By.CSS_SELECTOR, value=".meanings-wrapper")
            meanings_elements = meanings_container.find_elements(by=By.CSS_SELECTOR, value=".meaning-meaning")
            
            for element in meanings_elements:

                # excluding "other forms"
                break_units = element.find_elements(by=By.CSS_SELECTOR, value="span.break-unit")
                if len(break_units) > 0:
                    break

                # checking length and appending if there's room
                if len(word_meanings) >= self.meaning_count:
                    break
                word_meanings.append(element.text.split("; ")[0])

            # adding word
            words.append({
                "word" : word,
                "furigana" : furigana,
                "meanings" : word_meanings
            })

        # returning
        return all_kunyomi, all_onyomi, meanings, words

    def scan_input(self):
        
        # reading file
        self.kanji = []
        with open("input.txt", "r", encoding="utf-8") as f:
            content = f.read()
            for char in content:
                if char >= chr(19968) and char <= chr(40879):
                    self.kanji.append(char)

        # creating set
        self.kanji_set = set(self.kanji)

# initializing
word_count = input("How many words would you like to gather for each kanji found?\n")
meaning_count = input("How many meanings would you like to gather for each word and kanji?\n")
Main(int(word_count), int(meaning_count))