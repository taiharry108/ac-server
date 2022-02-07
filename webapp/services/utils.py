def convert_url(url: str, domain: str):
    if url.startswith("//"):
        result = "https:" + url
    elif not url.startswith("http"):
        result = domain + url.lstrip("/")
    else:
        result = url
    return result
    
