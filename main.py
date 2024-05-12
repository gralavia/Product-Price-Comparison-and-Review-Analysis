import requests
from bs4 import BeautifulSoup
import json
import os
import urllib.request
from openai import OpenAI


def crawl_momo(urls):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com'}

    session = requests.Session()
    momo_data = []
    for url in urls:
        response = session.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        product_name = soup.find("a", class_="productName").text
        price = soup.find("span", class_="seoPrice").text
        image_url = soup.find("img", class_="jqzoom").get("src")
        product_info = {"product_name": product_name, "price": price, "image_url": image_url}
        momo_data.append(product_info)
        image_filename = os.path.basename(image_url)
        urllib.request.urlretrieve(image_url, image_filename)
    return momo_data

def crawl_pinkoi(urls):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com'}

    session = requests.Session()
    pinkoi_data = []
    for url in urls:
        response = session.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        product_name = soup.find("h1", class_="title translate").text
        price = soup.find("span", class_="amount").text
        image_element = soup.find("img", class_="js-main-item-photo main-photo")
        if image_element:
            image_url = "https:" + image_element.get("src")
            product_info = {"product_name": product_name, "price": price, "image_url": image_url}
            pinkoi_data.append(product_info)
            image_filename = os.path.basename(image_url)
            urllib.request.urlretrieve(image_url, image_filename)
        else:
            print("No image found for", product_name)
    return pinkoi_data

def crawl_amazon_reviews(product_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com'}

    session = requests.Session()
    response = session.get(product_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    reviews = soup.find_all("span", class_="a-size-base review-text")  
    res_review = ""
    for review in reviews:
        res_review += review.text
    ratings = soup.find("span", class_="a-size-base a-color-base").text  

    return res_review, ratings

def main():
    momo_urls = [
		"product url1",
		"product url2"]
    pinkoi_urls = ["product url1", "product url2"]

    all_products_data = []

    for momo_url, pinkoi_url in zip(momo_urls, pinkoi_urls):
        momo_data = crawl_momo([momo_url])
        pinkoi_data = crawl_pinkoi([pinkoi_url])

        if momo_data and pinkoi_data:  
            momo_price = momo_data[0]["price"].replace(",", "")  
            pinkoi_price = pinkoi_data[0]["price"].replace(",", "")  

            momo_price = float(momo_price)
            pinkoi_price = float(pinkoi_price)

            cheaper_product = pinkoi_data[0] if pinkoi_price <= momo_price else momo_data[0]
            cheaper_url = pinkoi_url if pinkoi_price <= momo_price else momo_url

            amazon_url = "product url"
            res_review, ratings = crawl_amazon_reviews(amazon_url)

            client = OpenAI(api_key="<api_key>")
            prompt = "Provide pros and cons about the product：\n" + res_review
            response = client.completions.create(
				model="gpt-3.5-turbo-instruct",
				prompt=prompt,
			)

            text = response.choices[0].text.strip()
            pros_start_index = text.find("pros:")
            cons_start_index = text.find("cons:")
            pros = text[pros_start_index + len("pros:"):cons_start_index].strip().split("\n")
            cons = text[cons_start_index + len("cons:"):].strip().split("\n")

            cheaper_product["amazon_reviews"] = {"pros": pros, "cons": cons, "ratings": ratings}

            all_products_data.append(
				{"cheaper_product": cheaper_product, "cheaper_url": cheaper_url})
        else:
            print("Failed to retrieve data for one of the products.")

    with open("product_data.json", "w", encoding='utf-8') as f:
        json.dump(all_products_data, f, ensure_ascii=False, indent=4)
if __name__ == "__main__":
    main()
