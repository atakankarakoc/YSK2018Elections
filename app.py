import time
import os
import json as j
import pandas as pd
from flask import Flask
from flask import render_template
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


app = Flask(__name__)
current_directory = os.getcwd()
folder_path = os.path.join(current_directory, "json")

def fetch():
    options = webdriver.ChromeOptions()
    service = Service(ChromeDriverManager().install())
    json_f = {'download.default_directory': folder_path}
    options.add_experimental_option('prefs', json_f)
    browser = webdriver.Chrome(service=service, options=options)
    browser.maximize_window()

    # Login to Website
    link = "https://acikveri.ysk.gov.tr/anasayfa"
    browser.get(link)
    time.sleep(2)

    # Close the photo
    browser.find_element(by=By.CSS_SELECTOR, value="#myModalClose").click()
    time.sleep(2)

    # Click the select button
    choose_election = browser.find_element(by=By.ID, value="navbarDropdown")
    browser.execute_script("arguments[0].click();", choose_election)
    time.sleep(2)

    # Click on the title (Cumhurbaşkanı Seçimi)
    find_election = browser.find_element(by=By.CSS_SELECTOR, value="div#heading6 > h5 > a")
    find_election.click()
    time.sleep(1)

    # Choosing the 2018 Election
    browser.find_element(by=By.CSS_SELECTOR, value="#collapse6:nth-child(4)").click()
    time.sleep(3)

    # Clicking results from the left menu
    election_result = browser.find_elements(by=By.CSS_SELECTOR, value="#accordionSidebar > li.nav-item > a")
    for result in election_result:
        if result.text == "Cumhurbaşkanlığı Seçim Sonuçları":
            result.click()
            break

    time.sleep(4)
    json(browser)
    browser.quit()


def json(b):
    folder_contents = os.listdir(folder_path)
    # If the files have been downloaded, do not download them again.
    if len(folder_contents) == 0:
        json_district = "SecimSonucIlce.json"

        # Download of overall results
        b.find_element(by=By.CSS_SELECTOR, value="div.card-body>div>button:nth-child(2)").click()
        time.sleep(1)
        # A loop for download the overall results of the provinces
        for i in range(1, 82):
            try:
                if i == 7:
                    b.find_element(by=By.CSS_SELECTOR, value="#map>svg>g>text:nth-child(89)").click()
                    time.sleep(2)
                elif i == 35:
                    b.find_element(by=By.CSS_SELECTOR, value="#map>svg>g>text:nth-child(122)").click()
                    time.sleep(2)
                else:
                    # Choose a province step by step
                    element = b.find_element(by=By.CSS_SELECTOR, value=f"svg.country-svg > g > path[il_id='{i}']")
                    actions = ActionChains(b)
                    actions.move_to_element(element).click().perform()
                    time.sleep(2)

                # Download a json file for the selected region
                b.find_element(by=By.CSS_SELECTOR, value="div.card-body>div>button:nth-child(2)").click()
                time.sleep(2)

                # Rename json file
                files = os.listdir(folder_path)
                for file_name in files:
                    if file_name == json_district:
                        new_name = f"SecimSonucIlce{i}"
                        old_file_path = os.path.join(folder_path, json_district)
                        new_file_path = os.path.join(folder_path, new_name)
                        os.replace(old_file_path, new_file_path)

                # Click to return to previous page
                b.find_element(by=By.CSS_SELECTOR, value="button.icon-button:nth-child(2)").click()
                time.sleep(2)
            except:
                print("Something went wrong")
    else:
        return

def zip_to_list(col1, col2):
    return list(zip(col1, col2))

def dictionary(col1, col2):
    return dict(zip(col1, col2))

def newjson(foldername):
    with open(f"{folder_path}/{foldername}", "r", encoding="utf-8") as file:
        data = j.load(file)
        columns = ["İlçe Id", "İlçe Adı", "Belde Adı", "Kayıtlı Seçmen Sayısı", "Oy Kullanan Seçmen Sayısı","Geçerli Oy Toplamı",
               " MUHARREM İNCE ", " MERAL AKŞENER ", " RECEP TAYYİP ERDOĞAN ", " SELAHATTİN DEMİRTAŞ ",
               " TEMEL KARAMOLLAOĞLU ", " DOĞU PERİNÇEK "]
    df_list = []
    for item in data:
        if not item["İlçe Id"]:
            continue

        ilce_id = item["İlçe Id"]
        ilce_name = item["İlçe Adı"]

        if ilce_id.isdigit() and isinstance(ilce_name, str):
            ilce_id_value = ilce_id
            ilce_name_value = ilce_name

        if not ilce_id.isdigit():
            item["İlçe Id"] = ilce_id_value
            item["İlçe Adı"] = ilce_name_value

            values = []
            values.append(item['İlçe Id'])
            values.append(item['İlçe Adı'])
            for col in columns[2: 8]:
                col_value = item[col]
                values.append(col_value)

            new_col = ["ILCE NO", "ILCE ADI", "MUHARREM İNCE", "MERAL AKŞENER", "RECEP TAYYİP ERDOĞAN", "SELAHATTİN DEMİRTAŞ",
                       "TEMEL KARAMOLLAOĞLU", "DOĞU PERİNÇEK"]

            df_temp = pd.DataFrame([values], columns=new_col)
            df_list.append(df_temp)

    ilce = pd.concat(df_list, ignore_index=True)
    return ilce

@app.route("/")
def index():
    fetch()

    with open(f"{folder_path}/SecimSonucIl.json", "r", encoding="utf-8") as file:
        data = j.load(file)
    columns = ["İl Id", "İl Adı", "Kayıtlı Seçmen Sayısı", "Oy Kullanan Seçmen Sayısı", "Geçerli Oy Toplamı",
               " MUHARREM İNCE ", " MERAL AKŞENER ", " RECEP TAYYİP ERDOĞAN ", " SELAHATTİN DEMİRTAŞ ", " TEMEL KARAMOLLAOĞLU ",
               " DOĞU PERİNÇEK "]

    df_list = []

    # Reading the JSON data line by line
    for item in data:
        il_id = item["İl Id"]
        il_name = item["İl Adı"]
        if il_id.isdigit():
            il_id_value = il_id
            il_name_value = il_name

        # If "İl Id" equals a number, skip the line
        if not il_id.isdigit():
            item["İl Id"] = il_id_value

            values = []
            values.append(item['İl Id'])
            values.append(il_name_value)
            for col in columns[1: 7]:
                col_value = item[col]
                values.append(col_value)

            new_col = ["IL NO", "IL ADI", "MUHARREM İNCE", "MERAL AKŞENER", "RECEP TAYYİP ERDOĞAN", "SELAHATTİN DEMİRTAŞ", "TEMEL KARAMOLLAOĞLU",
                       "DOĞU PERİNÇEK"]

            df_temp = pd.DataFrame([values], columns=new_col)
            df_list.append(df_temp)

    city = pd.concat(df_list, ignore_index=True)
    return render_template("index.html",
                           title="Türkiye Seçim Sonuçları",
                           city=city,
                           ince=dictionary(city["IL NO"], city["MUHARREM İNCE"]),
                           meral=dictionary(city["IL NO"], city["MERAL AKŞENER"]),
                           rte=dictionary(city["IL NO"], city["RECEP TAYYİP ERDOĞAN"]),
                           selo=dictionary(city["IL NO"], city["SELAHATTİN DEMİRTAŞ"]),
                           temel=dictionary(city["IL NO"], city["TEMEL KARAMOLLAOĞLU"]),
                           dogu=dictionary(city["IL NO"], city["DOĞU PERİNÇEK"])
                           )

@app.route("/Adana")
def adana():
    ilce = newjson("SecimSonucIlce1")
    return render_template("/Adana.html",
                           title="Adana Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Adıyaman")
def adiyaman():
    ilce = newjson("SecimSonucIlce2")
    return render_template("Adıyaman.html",
                           title="Adıyaman Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Afyonkarahisar")
def afyonkarahisar():
    ilce = newjson("SecimSonucIlce3")
    return render_template("Afyonkarahisar.html",
                           title="Afyonkarahisar Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Ağrı")
def agri():
    ilce = newjson("SecimSonucIlce4")
    return render_template("Ağrı.html",
                           title="Ağrı Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Amasya")
def amasya():
    ilce = newjson("SecimSonucIlce5")
    return render_template("Amasya.html",
                           title="Amasya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Ankara")
def ankara():
    ilce = newjson("SecimSonucIlce6")
    return render_template("Ankara.html",
                           title="Ankara Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Antalya")
def antalya():
    ilce = newjson("SecimSonucIlce7")
    return render_template("Antalya.html",
                           title="Antalya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Artvin")
def artvin():
    ilce = newjson("SecimSonucIlce8")
    return render_template("Artvin.html",
                           title="Artvin Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Aydın")
def aydin():
    ilce = newjson("SecimSonucIlce9")
    return render_template("Aydın.html",
                           title="Aydın Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Balıkesir")
def balikesir():
    ilce = newjson("SecimSonucIlce10")
    return render_template("Balıkesir.html",
                           title="Balıkesir Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bilecik")
def bilecik():
    ilce = newjson("SecimSonucIlce11")
    return render_template("Bilecik.html",
                           title="Bilecik Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bingöl")
def bingol():
    ilce = newjson("SecimSonucIlce12")
    return render_template("Bingöl.html",
                           title="Bingöl Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bitlis")
def bitlis():
    ilce = newjson("SecimSonucIlce13")
    return render_template("Bitlis.html",
                           title="Bitlis Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bolu")
def bolu():
    ilce = newjson("SecimSonucIlce14")
    return render_template("Bolu.html",
                           title="Bolu Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Burdur")
def burdur():
    ilce = newjson("SecimSonucIlce15")
    return render_template("Burdur.html",
                           title="Burdur Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bursa")
def bursa():
    ilce = newjson("SecimSonucIlce16")
    return render_template("Bursa.html",
                           title="Bursa Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Çanakkale")
def canakkale():
    ilce = newjson("SecimSonucIlce17")
    return render_template("Çanakkale.html",
                           title="Çanakkale Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Çankırı")
def cankiri():
    ilce = newjson("SecimSonucIlce18")
    return render_template("Çankırı.html",
                           title="Çankırı Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Çorum")
def corum():
    ilce = newjson("SecimSonucIlce19")
    return render_template("Çorum.html",
                           title="Çorum Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Denizli")
def denizli():
    ilce = newjson("SecimSonucIlce20")
    return render_template("Denizli.html",
                           title="Denizli Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Diyarbakır")
def diyarbakir():
    ilce = newjson("SecimSonucIlce21")
    return render_template("Diyarbakır.html",
                           title="Diyarbakır Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Edirne")
def edirne():
    ilce = newjson("SecimSonucIlce22")
    return render_template("Edirne.html",
                           title="Edirne Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Elazığ")
def elazig():
    ilce = newjson("SecimSonucIlce23")
    return render_template("Elazığ.html",
                           title="Elazığ Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Erzincan")
def erzincan():
    ilce = newjson("SecimSonucIlce24")
    return render_template("Erzincan.html",
                           title="Erzincan Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Erzurum")
def erzurum():
    ilce = newjson("SecimSonucIlce25")
    return render_template("Erzurum.html",
                           title="Erzurum Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Eskişehir")
def eskisehir():
    ilce = newjson("SecimSonucIlce26")
    return render_template("Eskişehir.html",
                           title="Eskişehir Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Gaziantep")
def gaziantep():
    ilce = newjson("SecimSonucIlce27")
    return render_template("Gaziantep.html",
                           title="Gaziantep Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Giresun")
def giresun():
    ilce = newjson("SecimSonucIlce28")
    return render_template("Giresun.html",
                           title="Giresun Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Gümüşhane")
def gumushane():
    ilce = newjson("SecimSonucIlce29")
    return render_template("Gümüşhane.html",
                           title="Gümüşhane Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Hakkari")
def hakkari():
    ilce = newjson("SecimSonucIlce30")
    return render_template("Hakkari.html",
                           title="Hakkari Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Hatay")
def hatay():
    ilce = newjson("SecimSonucIlce31")
    return render_template("Hatay.html",
                           title="Hatay Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Isparta")
def isparta():
    ilce = newjson("SecimSonucIlce32")
    return render_template("Isparta.html",
                           title="Isparta Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Mersin")
def mersin():
    ilce = newjson("SecimSonucIlce33")
    return render_template("Mersin.html",
                           title="Mersin Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/İstanbul")
def istanbul():
    ilce = newjson("SecimSonucIlce34")
    return render_template("İstanbul.html",
                           title="İstanbul Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/İzmir")
def izmir():
    ilce = newjson("SecimSonucIlce35")
    return render_template("İzmir.html",
                           title="İzmir Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kars")
def kars():
    ilce = newjson("SecimSonucIlce36")
    return render_template("Kars.html",
                           title="Kars Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kastamonu")
def kastamonu():
    ilce = newjson("SecimSonucIlce37")
    return render_template("Kastamonu.html",
                           title="Kastamonu Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kayseri")
def kayseri():
    ilce = newjson("SecimSonucIlce38")
    return render_template("Kayseri.html",
                           title="Kayseri Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kırklareli")
def kirklareli():
    ilce = newjson("SecimSonucIlce39")
    return render_template("Kırklareli.html",
                           title="Kırklareli Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kırşehir")
def kirsehir():
    ilce = newjson("SecimSonucIlce40")
    return render_template("Kırşehir.html",
                           title="Kırşehir Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kocaeli")
def kocaeli():
    ilce = newjson("SecimSonucIlce41")
    return render_template("Kocaeli.html",
                           title="Kocaeli Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Konya")
def konya():
    ilce = newjson("SecimSonucIlce42")
    return render_template("Konya.html",
                           title="Konya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kütahya")
def kutahya():
    ilce = newjson("SecimSonucIlce43")
    return render_template("Kütahya.html",
                           title="Kütahya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Malatya")
def malatya():
    ilce = newjson("SecimSonucIlce44")
    return render_template("Malatya.html",
                           title="Malatya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Manisa")
def manisa():
    ilce = newjson("SecimSonucIlce45")
    return render_template("Manisa.html",
                           title="Manisa Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kahramanmaraş")
def kahramanmaras():
    ilce = newjson("SecimSonucIlce46")
    return render_template("Kahramanmaraş.html",
                           title="Kahramanmaraş Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Mardin")
def mardin():
    ilce = newjson("SecimSonucIlce47")
    return render_template("Mardin.html",
                           title="Mardin Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Muğla")
def mugla():
    ilce = newjson("SecimSonucIlce48")
    return render_template("Muğla.html",
                           title="Muğla Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Muş")
def mus():
    ilce = newjson("SecimSonucIlce49")
    return render_template("Muş.html",
                           title="Muş Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Nevşehir")
def nevsehir():
    ilce = newjson("SecimSonucIlce50")
    return render_template("Nevşehir.html",
                           title="Nevşehir Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Niğde")
def nigde():
    ilce = newjson("SecimSonucIlce51")
    return render_template("Niğde.html",
                           title="Niğde Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Ordu")
def ordu():
    ilce = newjson("SecimSonucIlce52")
    return render_template("Ordu.html",
                           title="Ordu Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Rize")
def rize():
    ilce = newjson("SecimSonucIlce53")
    return render_template("Rize.html",
                           title="Rize Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Sakarya")
def sakarya():
    ilce = newjson("SecimSonucIlce54")
    return render_template("Sakarya.html",
                           title="Sakarya Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Samsun")
def samsun():
    ilce = newjson("SecimSonucIlce55")
    return render_template("Samsun.html",
                           title="Samsun Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Siirt")
def siirt():
    ilce = newjson("SecimSonucIlce56")
    return render_template("Siirt.html",
                           title="Siirt Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Sinop")
def sinop():
    ilce = newjson("SecimSonucIlce57")
    return render_template("Sinop.html",
                           title="Sinop Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Sivas")
def sivas():
    ilce = newjson("SecimSonucIlce58")
    return render_template("Sivas.html",
                           title="Sivas Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Tekirdağ")
def tekirdag():
    ilce = newjson("SecimSonucIlce59")
    return render_template("Tekirdağ.html",
                           title="Tekirdağ Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Tokat")
def tokat():
    ilce = newjson("SecimSonucIlce60")
    return render_template("Tokat.html",
                           title="Tokat Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Trabzon")
def trabzon():
    ilce = newjson("SecimSonucIlce61")
    return render_template("Trabzon.html",
                           title="Trabzon Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Tunceli")
def tunceli():
    ilce = newjson("SecimSonucIlce62")
    return render_template("Tunceli.html",
                           title="Tunceli Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Şanlıurfa")
def sanliurfa():
    ilce = newjson("SecimSonucIlce63")
    return render_template("Şanlıurfa.html",
                           title="Şanlıurfa Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Uşak")
def usak():
    ilce = newjson("SecimSonucIlce64")
    return render_template("Uşak.html",
                           title="Uşak Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Van")
def van():
    ilce = newjson("SecimSonucIlce65")
    return render_template("Van.html",
                           title="Van Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Yozgat")
def yozgat():
    ilce = newjson("SecimSonucIlce66")
    return render_template("Yozgat.html",
                           title="Yozgat Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Zonguldak")
def zonguldak():
    ilce = newjson("SecimSonucIlce67")
    return render_template("Zonguldak.html",
                           title="Zonguldak Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Aksaray")
def aksaray():
    ilce = newjson("SecimSonucIlce68")
    return render_template("Aksaray.html",
                           title="Aksaray Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bayburt")
def bayburt():
    ilce = newjson("SecimSonucIlce69")
    return render_template("Bayburt.html",
                           title="Bayburt Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Karaman")
def karaman():
    ilce = newjson("SecimSonucIlce70")
    return render_template("Karaman.html",
                           title="Karaman Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kırıkkale")
def kirikkale():
    ilce = newjson("SecimSonucIlce71")
    return render_template("Kırıkkale.html",
                           title="Kırıkkale Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Batman")
def batman():
    ilce = newjson("SecimSonucIlce72")
    return render_template("Batman.html",
                           title="Batman Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Şırnak")
def sirnak():
    ilce = newjson("SecimSonucIlce73")
    return render_template("Şırnak.html",
                           title="Şırnak Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Bartın")
def bartin():
    ilce = newjson("SecimSonucIlce74")
    return render_template("Bartın.html",
                           title="Bartın Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Ardahan")
def ardahan():
    ilce = newjson("SecimSonucIlce75")
    return render_template("Ardahan.html",
                           title="Ardahan Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Iğdır")
def igdir():
    ilce = newjson("SecimSonucIlce76")
    return render_template("Iğdır.html",
                           title="Iğdır Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Yalova")
def yalova():
    ilce = newjson("SecimSonucIlce77")
    return render_template("Yalova.html",
                           title="Yalova Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Karabük")
def karabuk():
    ilce = newjson("SecimSonucIlce78")
    return render_template("Karabük.html",
                           title="Karabük Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Kilis")
def kilis():
    ilce = newjson("SecimSonucIlce79")
    return render_template("Kilis.html",
                           title="Kilis Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Osmaniye")
def osmaniye():
    ilce = newjson("SecimSonucIlce80")
    return render_template("Osmaniye.html",
                           title="Osmaniye Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

@app.route("/Düzce")
def duzce():
    ilce = newjson("SecimSonucIlce81")
    return render_template("Düzce.html",
                           title="Düzce Seçim Sonuçları",
                           ilce=ilce,
                           ince=zip_to_list(ilce["ILCE NO"], ilce["MUHARREM İNCE"]),
                           meral=zip_to_list(ilce["ILCE NO"], ilce["MERAL AKŞENER"]),
                           rte=zip_to_list(ilce["ILCE NO"], ilce["RECEP TAYYİP ERDOĞAN"]),
                           selo=zip_to_list(ilce["ILCE NO"], ilce["SELAHATTİN DEMİRTAŞ"]),
                           temel=zip_to_list(ilce["ILCE NO"], ilce["TEMEL KARAMOLLAOĞLU"]),
                           dogu=zip_to_list(ilce["ILCE NO"], ilce["DOĞU PERİNÇEK"])
                           )

if __name__ == "__main__":
    app.run()
