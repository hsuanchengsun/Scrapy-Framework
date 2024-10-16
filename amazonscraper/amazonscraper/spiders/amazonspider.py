import scrapy
from urllib.parse import urlencode


class AmazonspiderSpider(scrapy.Spider):
    name = "amazonspider"
    allowed_domains = ["www.amazon.com", ""]
    start_urls = [""]

    # Scrape the product list from the product list page
    def parse(self, response):
        for product in response.css("div.s-result-item[data-component-type=s-search-result]"):
            relative_url = product.css("h2>a::attr(href)").get()
            asin = relative_url.split('/')[3] if len(relative_url.split('/')) >= 4 else None
            product_url = f"https://www.amazon.com/dp/{asin}"

            yield scrapy.Request(url=product_url, callback=self.parse_product, meta={
                'asin': asin,
                'product_url': product_url
            })

        # Extract the URL for the next page

        next_page_url = response.css('a.s-pagination-next::attr(href)').get()
        if next_page_url:
            yield scrapy.Request(url=response.urljoin(next_page_url), callback=self.parse)

    # Scrape necessary product information from the product page
    def parse_product(self, response):
        title = response.css("h1>span::text").get().strip()
        regular_price = response.css('span.apexPriceToPay span.a-offscreen::text').extract_first()
        sub_price = response.css('#snsPriceRow #sns-base-price::text').extract_first()
        total_ratings = response.css('span#acrCustomerReviewText::text').extract_first().split(' ')[0].replace(',', '')
        rating = response.css('span#acrPopover span.a-icon-alt::text').extract_first().split(' ')[0]

        top_part_key = [k.replace(':\n', '').strip() for k in response.css('div.a-row label.a-form-label::text').extract()]
        top_part_value = [v.strip() for v in response.css('div.a-row span.selection::text').extract()]
        top_part = dict(zip(top_part_key, top_part_value))
        style = top_part.get('Style', "")
        flavor_name = top_part.get('Flavor Name', "")
        size = top_part.get('Size', "")

        bottom_part_extract = response.css('span.a-size-base.a-text-bold::text').extract()
        keys = ['Brand', 'Flavor', 'Age Range (Description)', 'Item Form', 'Specific Uses For Product']
        bottom_part_key = [i for i in bottom_part_extract if i in keys]
        bottom_part_value = response.css('span.a-size-base.po-break-word::text').extract()
        bottom_part = dict(zip(bottom_part_key, bottom_part_value))
        brand = bottom_part.get('Brand', "")
        flavor = bottom_part.get('Flavor', "")
        age_range = bottom_part.get('Age Range (Description)', "")
        item_form = bottom_part.get('Item Form', "")
        specific_use = bottom_part.get('Specific Uses For Product', "")

        ingredients = response.css('#nic-ingredients-content span.a-size-base::text').get()
        about = response.css('#feature-bullets ul.a-unordered-list li span.a-list-item::text').getall()

        asin = response.meta['asin']
        product_url = response.meta['product_url']

        yield {
            'Title': title,
            'Regular Price': regular_price,
            'Subscription Price': sub_price,
            'Total Ratings': total_ratings,
            'Rating': rating,
            'Style': style,
            'Flavor Name': flavor_name,
            'Size': size,
            'Brand': brand,
            'Flavor': flavor,
            'Age Range': age_range,
            'Item Form': item_form,
            'Specific Use': specific_use,
            'Ingredients': ingredients,
            'About': about,
            'ASIN': asin,
            'Product URL': product_url
        }