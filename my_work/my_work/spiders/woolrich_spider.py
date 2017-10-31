import re
from scrapy import FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class WoolRichSpider(CrawlSpider):

    name = 'woolrich'
    allowed_domains = ['woolrich.com']
    start_urls = ['http://www.woolrich.com']
    skus_url = "http://www.woolrich.com/woolrich/prod/fragments/productDetails.jsp"
    navigation_css = ['.mobile-menu-list.default', '.nav-list', '.addMore']
    product_css = ['.hover_img']
    rules = (
        Rule(LinkExtractor(restrict_css=navigation_css, tags=('a', 'div'), attrs=('href', 'nextpage')),),
        Rule(LinkExtractor(restrict_css=product_css), callback='parse_product'),
    )

    def parse_product(self, response):
        product = {}
        product['skus'] = {}
        product['requests'] = []
        product['name'] = self.product_name(response)
        product['description'] = self.product_description(response)
        product['retailer_sku'] = self.product_retailer_sku(response)
        product['currency'] = self.product_currency(response)
        product['url'] = self.product_url(response)
        product['original_url'] = self.product_original_url(response)
        product['category'] = self.product_categories(response)
        product['care'] = self.product_care(response)
        product['trail'] = self.product_trail(response)
        product['image_urls'] = self.porduct_image_urls(response)
        colors = self.product_color_ids(response)
        product['requests'] += self.color_request(product, colors)
        return self.request_or_product(product)

    def parse_size(self, response):
        sku_ids = self.product_sku_ids(response, selector="sizelist")
        dimensions = self.product_dimensions(response)
        response.meta['product']['requests'] += self.size_request(response, sku_ids, dimensions)
        return self.request_or_product(response.meta['product'])

    def parse_fit(self, response):
        sku_ids = self.product_sku_ids(response, selector="dimensionslist")
        response.meta['product']['requests'] += self.fit_request(response, sku_ids)
        return self.request_or_product(response.meta['product'])

    def parse_skus(self, response):
        dimension = ""
        currency = self.sku_currency(response)
        price = self.sku_price(response)
        color = self.sku_color(response)
        sku_id = self.sku_id(response, selector="dimensionslist")
        if sku_id:
            size = self.sku_size(response)
            dimension = self.sku_dimension(response)
        else:
            sku_id = self.sku_id(response, selector="sizelist")
            size = self.sku_size(response)
        if dimension:
            size = size + "/" + dimension.strip()
        response.meta['product']['skus'][sku_id] = {
            "currency": currency,
            "price": price,
            "color": color,
            "size": size
        }
        return self.request_or_product(response.meta['product'])

    def product_name(self, response):
        return response.css('.pdp_title [itemprop="name"]::text').extract_first().strip()

    def product_description(self, response):
        description_css = 'span[itemprop="description"]::text, span[itemprop="description"] li::text'
        return response.css(description_css).extract()

    def product_retailer_sku(self, response):
        return response.css('.pdp::attr(productid)').extract_first()

    def product_url(self, response):
        return response.css('link[rel="canonical"]::attr(href)').extract_first()

    def product_original_url(self, response):
        return response.url

    def product_care(self, response):
        return response.css('label[for="feature"] + div li::text').extract()

    def product_currency(self, response):
        return response.css('[itemprop="priceCurrency"]::text').extract_first()

    def product_categories(self, response):
        return response.css('#breadcrumbs a::text').extract()[1:]

    def product_trail(self, response):
        trail_urls = response.css('#breadcrumbs a::attr(href)').extract()
        return [response.urljoin(trail_url) for trail_url in trail_urls]

    def porduct_image_urls(self, response):
        image_urls = response.css('#prod-detail__slider-nav img::attr(src)').extract()
        urls = [response.urljoin(image_url) for image_url in image_urls]
        return urls if urls else [response.urljoin(response.css('#largeImg::attr(src)').extract_first())]

    def product_color_ids(self, response):
        return response.css(".colorlist a:not([class~='disabled']) img::attr(colorid)").extract()

    def product_sku_ids(self, response, selector):
        return response.xpath('//ul[@class="' + selector + '"]/li/a[@stocklevel>0]/@id').extract()

    def product_dimensions(self, response):
        return response.css(".dimensionslist a").extract()

    def sku_id(self, response, selector):
        return response.css('.' + selector + ' a[class~="selected"]::attr(id)').extract_first()

    def sku_currency(self, response):
        return response.css('[itemprop="priceCurrency"]::attr(content)').extract_first()

    def sku_price(self, response):
        return response.css('[itemprop="price"]::attr(content)').extract_first()

    def sku_color(self, response):
        return response.css('.colorName::text').extract_first().strip()

    def sku_size(self, response):
        return response.css('.sizelist a[class~="selected"]::attr(title)').extract_first()

    def sku_dimension(self, response):
        return response.css('.dimensionslist a[class~="selected"]::text').extract_first().strip()

    def color_request(self, product, colors):
        requests = []
        for color_id in colors:
            product_id = product['retailer_sku']
            data = {'productId': product_id, 'colorId': color_id}
            request = self.request(data, self.parse_size, product)
            requests.append(request)
        return requests

    def size_request(self, response, sku_ids, dimensions):
        requests = []
        for sku_id_or_size in sku_ids:
            request_parameters = response.request.body.decode()
            product_id = response.meta['product']['retailer_sku']
            color_id = "".join(re.findall("[A-Z]{3}", request_parameters))
            if dimensions:
                data = {'productId': product_id, 'colorId': color_id, 'selectedSize': sku_id_or_size}
                request = self.request(data, self.parse_fit, response.meta['product'])
            else:
                data = {'productId': product_id, 'colorId': color_id, 'skuId': sku_id_or_size}
                request = self.request(data, self.parse_skus, response.meta['product'])
            requests.append(request)
        return requests

    def fit_request(self, response, sku_ids):
        requests = []
        for sku_id in sku_ids:
            product_id = response.meta['product']['retailer_sku']
            data = {'productId': product_id, 'skuId': sku_id}
            request = self.request(data, self.parse_skus, response.meta['product'])
            requests.append(request)
        return requests

    def request(self, formdata_, callback_, product):
        return FormRequest(url=self.skus_url, formdata=formdata_, callback=callback_,
                           meta={'product': product})

    def request_or_product(self, product):
        if product['requests']:
            return product['requests'].pop()
        return product
