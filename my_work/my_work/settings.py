BOT_NAME = 'my_work'

SPIDER_MODULES = ['my_work.spiders']
NEWSPIDER_MODULE = 'my_work.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 3

DOWNLOADER_MIDDLEWARES = {
    'my_work.middlewares.ForceUTF8ResponseMiddleware': 400,
    'my_work.middlewares.FixMalformedUrlMiddleware': 600,
}

ITEM_PIPELINES = {
    'my_work.pipelines.RetailerskuShouldNeverBeEmpty': 301,
    'my_work.pipelines.NoNewlineInImportantFields': 310,
    'my_work.pipelines.CleanProtocolRelativeUrls': 311,
}
