from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import time

# main clas
class Main():
    def __init__(self, word_count=3, meaning_count=4):

        # constants
        self.WORD_COUNT = word_count
        self.MEANING_COUNT = meaning_count

        # creating driver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

        # main properties
        self.kanji = []
        self.kanji_set = {}

        # scanning input
        self.scan_input()
        self.generate_csv()

    def generate_quiz_csv(self):
        kanji_data = self.get_kanji_data()
        
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
        print("Finished gathering kanji data")
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
        meanings = meanings_container.text.replace(" ", "").split(",")

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
            if len(words) >= self.WORD_COUNT:
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
                if len(word_meanings) >= self.MEANING_COUNT:
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
meaning_count = input("How many meanings would you like to gather for each word?\n")
file_name = input("What would you like to call the output file? It will be set in the .csv file format, so don't include the file format in yoru answer.\n")
Main(int(word_count), int(meaning_count), file_name)