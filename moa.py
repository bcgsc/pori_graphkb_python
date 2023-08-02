import requests

url = "https://moalmanac.org/api/assertions"
moa_lst = [
    72, 292, 293, 429, 431, 430, 289, 537, 557, 566, 567, 306, 291, 576
]

def fnc1(assertion):
    for feature in assertion['features']:
        if feature['feature_type'] == 'somatic_variant':
            return True
    return False

res = requests.get(url)
moa = res.json()

moa_filtered = filter(lambda x: x['assertion_id'] in moa_lst, moa)
moa_filtered2 = filter(fnc1, moa)

for i in moa_filtered:
    assertion_id = i['assertion_id']
    feature_type = [j['feature_type'] for j in i['features']]
    print(assertion_id, feature_type)

for i in moa_filtered2:
    print(i['assertion_id'])