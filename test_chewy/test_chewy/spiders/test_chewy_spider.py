import scrapy
import re


class ChewyitemspiderSpider(scrapy.Spider):
    name = "test_chewy_spider"
    allowed_domains = ["www.chewy.com"]
    start_urls = [""]

    def parse(self, response):
        for product in response.css('div.kib-product-card'):
            brand = product.css('strong::text').get()
            price = product.css('div.kib-product-price::text').get()
            product_url = response.urljoin(product.css('a.kib-product-title::attr(href)').get())

            yield scrapy.Request(url=product_url, callback=self.parse_product, meta={
                'brand': brand,
                'price': price,
                'product_url': product_url
            })

        # Extract the URL for the next page
        next_page_url = response.css('a.kib-pagination-new-item--next::attr(href)').get()
        if next_page_url:
            yield scrapy.Request(url=response.urljoin(next_page_url), callback=self.parse)
    
    
    def parse_product(self, response):
        prod_cat = response.css(".kib-breadcrumbs-item__link::text").extract()
        prod_cat_str = ' / '.join(prod_cat)

        price = response.meta['price']
        product_url = response.meta['product_url']

        brand = response.css('span.styles_root__jnAwp a.styles_brandLink__MdoyO::text').get()
        product_name_full = response.css('h1.styles_productName__vSdxx::text').get()
        product_name = product_name_full.replace(brand, '').strip() if brand and product_name_full else product_name_full
        if "Bundle" in product_name:
            return
        
        unit_price = ''.join(response.css(".styles_ppuText__vJZmA::text").extract())

        labels_raw = response.css(".kib-form-dropdown__wrapper .kib-radio__label::text").extract()
        if labels_raw:
            labels = [label.strip() for label in labels_raw if label.strip() != ""]
            flavor_list = []
            package_list = []
            for label in labels:
                if re.search(r'\d', label):
                    package_list.append(label)
                else:
                    flavor_list.append(label)
        else: 
            data = response.css(".kib-swatch__text-swatch-header::text").extract()
            # Removing duplicates
            unique_data = list(set(data))

            # Separating values based on the presence of digits
            package_list = [item for item in unique_data if any(char.isdigit() for char in item)]
            flavor_list = [item for item in unique_data if not any(char.isdigit() for char in item)]

        # Extracting details from the bullet points
        item_highlight = response.css('#KEY_BENEFITS-section li::text')
        item_highlight_list = [item.get().strip() for item in item_highlight]

        # Extracting paragraph from the "See More" section
        see_more_paragraphs = response.css('.styles_infoGroupSection__ArCb9 p::text')
        paragraphs_list = [para.get().strip() for para in see_more_paragraphs]

        # Extracting specifications table
        specifications_keys = response.css('.styles_markdownTable__Mtq7h th::text')
        specifications_values = response.css('.styles_markdownTable__Mtq7h td::text')
        specifications_dict = dict(zip([key.get().strip() for key in specifications_keys], [value.get().strip() for value in specifications_values]))

        ingredients = response.css('#INGREDIENTS-section p::text').get()
        caloric = response.css('#CALORIC_CONTENT-section p::text').get()
        
        # Extracting guaranteed analysis table
        guaranteed_analysis_keys = response.css('#GUARANTEED_ANALYSIS-section th::text')
        guaranteed_analysis_values = response.css('#GUARANTEED_ANALYSIS-section td::text')
        guaranteed_analysis_dict = dict(zip([key.get().strip() for key in guaranteed_analysis_keys], [value.get().strip() for value in guaranteed_analysis_values]))
        
        
        yield {
            'Product Category': prod_cat_str,
            'Brand': brand,
            'Item Name': product_name,
            'Price': price,
            'Product Link': product_url,
            'Flavor List': flavor_list,
            'Package List': package_list,
            'Item Highlight': item_highlight_list,
            'Item Information': paragraphs_list[0],
            'Item Number': specifications_dict.get('Item Number', ""),
            'Made In': specifications_dict.get('Made In', ""),
            'Sourced From': specifications_dict.get('Sourced From', ""),
            'Lifestage': specifications_dict.get('Lifestage', ""),
            'Food Form': specifications_dict.get('Food Form', ""),
            'Special Diet': specifications_dict.get('Special Diet', ""),
            'Ingredients': ingredients,
            'Caloric Content': caloric,
            'Guaranteed Analysis': guaranteed_analysis_dict,
            
        }
