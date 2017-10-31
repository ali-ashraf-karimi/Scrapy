import json
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class KithSpider(CrawlSpider):
    name = 'kith'
    allowed_domains = ['kith.com']
    start_urls = ['https://kith.com/']
    force_utf8 = True
    fix_url = True

    rules = (

        Rule(LinkExtractor(allow=('/products',), restrict_css=(".product-card-main",)), callback='parse_item'),
        Rule(LinkExtractor(allow=('/collections/',)), follow=True),
    )

    def parse_item(self, response):
        product = dict()

        product['url'] = response.url
        product['brand'] = self.product_brand(response)
        product['category'] = self.product_category(response)

        description, care = self.product_description_and_care(response)
        product['description'] = description
        product['care'] = care
        product['image_urls'] = self.image_urls(response)
        product['market'] = 'US'

        sku_content = re.split(r"variants\":", self.get_sku_content(response))
        product['retailer_sku'] = self.retailer_sku(response)
        product['skus'] = self.skus(sku_content[1], response)
        product['gender'] = self.gender(sku_content[0])

        product['name'] = self.product_name(response)
        product['retailer'] = 'kith-us'

        return product

    def get_sku_content(self, response):
        pattern = re.compile('var product\s*=\s*(.*?),"images', re.MULTILINE | re.DOTALL)
        return response.xpath("//script[contains(.,'var product')]/text()").re(pattern)[0]

    def product_brand(self, response):
        return 'Kith'

    def product_category(self, response):
        return response.css('.breadcrumb a[href^="/c"]::text').extract()

    def product_name(self, response):
        return response.css('h1[itemprop=name] ::text').extract()

    def product_description_and_care(self, response):
        parent_class = response.css('.product-single-details-rte')
        description = parent_class.css('p::text').extract()[:-2]
        care = parent_class.css('p:last-child::text').extract()

        return description, care

    def image_urls(self, response):
        css = '.js-super-slider-photo-img::attr(src)'
        image_urls = response.css(css).extract()
        return [url.replace('.progressive', "") for url in image_urls]

    def gender(self, script):
        return "women" if "wmns" in script else "men"

    def retailer_sku(self, response):
        return response.css('#product_id::attr(value)').extract_first()

    def skus(self, script, response):
        variants = json.loads(script)
        skus = {}

        for variant in variants:
            sku = {}
            sku['price'] = variant['price']
            sku['currency'] = 'USD'
            sku['out_of_stock'] = not variant['available']

            if variant['compare_at_price']:
                sku['previous_prices'] = [variant['compare_at_price']]

            sku['size'] = variant['title']
            sku['colour'] = response.css('.-variant::text').extract_first().strip()
            skus[variant['id']] = sku

        return skus
