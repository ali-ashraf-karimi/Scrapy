class RetailerskuShouldNeverBeEmpty(object):

    def process_item(self, item, spider):
        if not item.get('retailer_sku'):
            raise DropItem('Garment can not have retailer_sku unset or empty!')

        return item


class CleanProtocolRelativeUrls(object):
    def process_item(self, item, spider):
        image_urls = item.get('image_urls', [])
        protocol_aware_images = []

        for img in image_urls:
            if img.startswith('//'):
                protocol_aware_images.append('http:{0}'.format(img))
            else:
                protocol_aware_images.append(img)

        item['image_urls'] = protocol_aware_images

        return item


class NoNewlineInImportantFields(object):
    """ Remove newlines from important fields, while we are at it,
        strip the string aswell """

    def __init__(self):
        self.important_fields = ['name', 'brand']

    def process_item(self, item, spider):
        for important_field in self.important_fields:
            if important_field in item:
                if type(item[important_field]) == list:
                    item[important_field] = item[important_field][0]
                item[important_field] = item[important_field].replace('\n', '').strip()
        return item
