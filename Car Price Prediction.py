import requests
from bs4 import BeautifulSoup
import mysql.connector
import csv
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

########################################################################################################################################################
def findBrandAndModelAndYear(carTitle, brand, model, year):
    if "Land Rover" in carTitle:
        year = int(carTitle[0:4])
        brand = "Land Rover"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    elif "Alpha Romeo" in carTitle:
        year = int(carTitle[0:4])
        brand = "Alpha Romeo"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    elif "Am General" in carTitle:
        year = int(carTitle[0:4])
        brand = "Am General"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    elif "American Motors" in carTitle:
        year = int(carTitle[0:4])
        brand = "American Motors"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    elif "Aston Martin" in carTitle:
        year = int(carTitle[0:4])
        brand = "Aston Martin"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    elif "Avanti Motors" in carTitle:
        year = int(carTitle[0:4])
        brand = "Avanti Motors"
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

    else:
        year = int(carTitle.split()[0])
        brand = carTitle.split()[1]
        model = carTitle[4 + len(brand) + 2:]
        return brand, model, year

########################################################################################################################################################
def readBrandsAndModelsAndYears(soup, brands, models, years):
    cars = soup.find_all(class_ = "title")

    brand = str()
    model = str()
    year = int()

    for car in cars:
        brand, model, year = findBrandAndModelAndYear(car.text, brand, model, year)
        brands.append(brand)
        models.append(model)
        years.append(year)

        brand = ""
        model = ""
        year = 0
    
    return brands, models, years

########################################################################################################################################################
def readMiles(soup, miles):
    cars = soup.find_all(class_ = "mileage")

    mile = str()

    for car in cars:
        for i in range(len(car.text)):
            if car.text[i] >= '0' and car.text[i] <= '9':
                mile = mile + car.text[i]
        miles.append(mile)
        mile = ""

    return miles

########################################################################################################################################################
def readPrices(soup, prices):
    cars = soup.find_all(class_ = "primary-price")

    price = str()

    for car in cars:
        for i in range(len(car.text)):
            if car.text[i] >= '0' and car.text[i] <= '9':
                price = price + car.text[i]
        prices.append(price)
        price = ""

    return prices

########################################################################################################################################################
def cleanLists(brands, models, years, miles, prices):
    for i in range(len(prices)):
        if prices[i] == "":
            del(brands[i])
            del(models[i])
            del(years[i])
            del(miles[i])
            del(prices[i])
            i -= 1
        if i == len(prices) - 1: break
    
    for i in range(len(brands)):
        miles[i] = int(miles[i])
        prices[i] = int(prices[i])
    
    return brands, models, years, miles, prices

########################################################################################################################################################
def readSite():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
        "Connection": "close",
        "Upgrade-Insecure-Requests": "1",
    }

    brands = []
    models = []
    years = []
    miles = []
    prices = []

    for pageNumber in range(1, 151):
        url = "https://www.cars.com/shopping/results/?page=" + str(pageNumber) + "&page_size=20&dealer_id=&keyword=&list_price_max=&list_price_min=&makes[]=&maximum_distance=20&mileage_max=&sort=best_match_desc&stock_type=used&year_max=&year_min=&zip=30334"
        response = requests.get(
            url.format(),
            headers=headers,
        )
        soup = BeautifulSoup(response.text, "html.parser")

        brands, models, years = readBrandsAndModelsAndYears(soup, brands, models, years)
        
        miles = readMiles(soup, miles)
        miles.remove('')
        
        prices = readPrices(soup, prices)

    for pageNumber in range(1, 51):
        url = "https://www.cars.com/shopping/results/?page=" + str(pageNumber) + "&page_size=20&dealer_id=&keyword=&list_price_max=&list_price_min=&makes[]=&maximum_distance=20&sort=best_match_desc&stock_type=new&year_max=&year_min=&zip=30334"
        response = requests.get(
            url.format(),
            headers=headers,
        )
        soup = BeautifulSoup(response.text, "html.parser")

        brandsBeforeLen = len(brands)
        brands, models, years = readBrandsAndModelsAndYears(soup, brands, models, years)
        brandsAfterLen = len(brands)

        prices = readPrices(soup, prices)
        
        for i in range(brandsAfterLen - brandsBeforeLen): miles.append('0')

    cleanLists(brands, models, years, miles, prices)

    return brands, models, years, miles, prices

########################################################################################################################################################
def saveInDatabase(brands, models, years, miles, prices, cnx, cursor):
    cursor.execute("CREATE TABLE cars (Brands VARCHAR(255), Models VARCHAR(255), Years INT, Miles INT, Prices INT)")

    for i in range(len(brands)):
        brand = brands[i]
        model = models[i]
        year = str(years[i])
        mile = str(miles[i])
        price = str(prices[i])
        cursor.execute("INSERT INTO cars (Brands, Models, Years, Miles, Prices) VALUES (%s, %s, %s, %s, %s)", (brand, model, year, mile, price))

    cnx.commit()
    cursor.close()
    cnx.close()

########################################################################################################################################################
def writeTempCSV(brands, models):
    data = list()

    header = ["Brand", "Model"]

    for i in range(len(brands)):
        data.append([brands[i], models[i]])

    with open('temp.csv', 'w', encoding='UTF8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

########################################################################################################################################################
def readTempCSV():
    dataframe = pd.read_csv('temp.csv')

    le = LabelEncoder()
    brandLabel = le.fit_transform(dataframe['Brand'])
    modelLabel = le.fit_transform(dataframe['Model'])

    return brandLabel, modelLabel

########################################################################################################################################################
def writeCarsCSV(brands, models, years, miles, prices):
    data = list()

    header = ["Brand", "Model", "Year", "Mile", "Price"]

    for i in range(len(brands)):
        data.append([brands[i], models[i], years[i], miles[i], prices[i]])
    
    brandChoice = data[len(brands) - 1][0]
    modelChoice = data[len(brands) - 1][1]
    yearChoice  = data[len(brands) - 1][2]
    mileChoice  = data[len(brands) - 1][3]

    del(data[len(brands) - 1])

    with open('cars.csv', 'w', encoding='UTF8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)
    
    return brandChoice, modelChoice, yearChoice, mileChoice

########################################################################################################################################################
def predictPrice(brandChoice, modelChoice, yearChoice, mileChoice):
    data = pd.read_csv("cars.csv")

    x = data.drop(columns = ["Price"])
    y = data["Price"]

    model = DecisionTreeClassifier()
    model.fit(x, y)

    prediction = model.predict([[brandChoice, modelChoice, yearChoice, mileChoice]])

    print("The price could be $%i" % prediction)

########################################################################################################################################################
def main():
    cnx = mysql.connector.connect(user = 'root', password = 'zbahramz2015', host = '127.0.0.1')
    cursor = cnx.cursor()

    DB_NAME = input("Please Enter Your Database Name: ")
    cursor.execute("CREATE DATABASE IF NOT EXISTS %s" % DB_NAME)

    brand = input("Please input a brand: ")
    mod = input("Please input a model: ")
    year = int(input("Please input a year: "))
    mile = int(input("Please input a mileage: "))

    cnx = mysql.connector.connect(user = 'root', password = 'zbahramz2015', host = '127.0.0.1', database = DB_NAME)
    cursor = cnx.cursor()

    cursor.execute("SHOW TABLES LIKE 'cars'")
    result = cursor.fetchone()
    if not result: 
        brands, models, years, miles, prices = readSite()
        
        saveInDatabase(brands, models, years, miles, prices, cnx, cursor)
    
    else:
        brands = []
        models = []
        years = []
        miles = []
        prices = []
    
        cursor.execute("SELECT * FROM cars")
        for (brand, model, year, mile, price) in cursor:
            brands.append(brand)
            models.append(model)
            years.append(int(year))
            miles.append(int(mile))
            prices.append(int(price))
        
    brands.append(brand)
    models.append(mod)
    years.append(year)
    miles.append(mile)
    prices.append(0)
    
    writeTempCSV(brands, models)
    brands, models = readTempCSV()
    brandChoice, modelChoice, yearChoice, mileChoice = writeCarsCSV(brands, models, years, miles, prices)

    predictPrice(brandChoice, modelChoice, yearChoice, mileChoice)

if __name__=="__main__":
    main()