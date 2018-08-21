import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import json
import time
import math
import csv
from haversine import haversine

def changeTime(allTime): # convert seconds into day, hour, minute
    day = 24*60*60
    hour = 60*60
    min = 60
    if allTime <60:        
        return  "%d sec"%math.ceil(allTime)
    elif  allTime > day:
        days = divmod(allTime,day) 
        return "%d days, %s"%(int(days[0]),changeTime(days[1]))
    elif allTime > hour:
        hours = divmod(allTime,hour)
        return '%d hours, %s'%(int(hours[0]),changeTime(hours[1]))
    else:
        mins = divmod(allTime,min)
        return "%d mins, %d sec"%(int(mins[0]),math.ceil(mins[1]))

def filter_inventor(r_all):
	i = 0
	q = 1
	p = 0
	while i<len(r_all):	
		while p < len(r_all[i]["inventors"]):
			if r_all[i]["inventors"][p]["inventor_location_id"] is None:
				del (r_all[i]["inventors"][p])
				p = p-1 
			p = p+1
		if len(r_all[i]["inventors"]) > 2:
			while q < len(r_all[i]["inventors"]):
				if r_all[i]["inventors"][0]["inventor_location_id"] == \
				r_all[i]["inventors"][1]["inventor_location_id"]:
					del r_all[i]["inventors"][1] 
				q = q + 1
			try: 
				del (r_all[i]["inventors"][2:])
			except: a = 1
        if len(r_all[i]["inventors"]) == 1:
        	del r_all[i]
        	i = i-1
		i = i+1
	return r_all

def add_distance(r_all):
	for i in range(0, len(r_all)):
		# print (r_all[i]["inventors"])
		lati1 = r_all[i]["inventors"][0]["inventor_location_id"].split("|")[0]
		long1 = r_all[i]["inventors"][0]["inventor_location_id"].split("|")[1]
		lati2 = r_all[i]["inventors"][1]["inventor_location_id"].split("|")[0]
		long2 = r_all[i]["inventors"][1]["inventor_location_id"].split("|")[1]
		point_a = (float(lati1),float(long1))
		point_b = (float(lati2),float(long2))
		distance = haversine(point_a,point_b)
		r_all[i]["distance"] = distance 
		r_all[i]["citation_times"] = len(r_all[i]["citedby_patents"])
		if r_all[i]["citedby_patents"][0]["citedby_patent_number"] is None:
			r_all[i]["citation_times"] = 0

if __name__=="__main__":
	smallest_num = 3930271 #found the smallest patent_id in the database
	max_num = 9999999
	url = "http://www.patentsview.org/api/patents/query"
	# body = {"q":{"_eq":{"patent_number":"8395459"}},
	# 	"f":["patent_id","patent_title","patent_date","patent_kind", 
	# 	"citedby_patent_number","inventor_key_id","inventor_location_id","inventor_city","inventor_state","inventor_country"],
	# 	"s":[{"patent_date":"desc"},{"patent_number":"asc"}],
	# 	"o":{"include_subentity_total_counts":"true"}}
	headers = {"Connection": "keep-alive","content-type":"application/json"}

	time_start=time.time()  
	# file = open('test.json','w')
	count = 1
	for i in range(1): # The total number of results shown in one page is 10000 at most
		if (i%10 == 0) & (count > 1):
			max_num = max_num - 200000  #sample 100000 patents in every 200000 patents
		print ("range is " + "[" + str(smallest_num) + "," + str(max_num) +"]")
		body = {"q":{"_and": [{"_lte":{"patent_number": max_num}},{"_gte":{"patent_number":smallest_num}}]},
		"f":["patent_id","patent_title","patent_date","patent_kind", 
		"citedby_patent_number","inventor_key_id","inventor_location_id"], #"inventor_city","inventor_state","inventor_country"
		"s":[{"patent_date":"desc"},{"patent_id":"asc"}], 
		"o":{"include_subentity_total_counts":"true","page":i%10+1,"per_page":10000}} # There are 100000 patents returned in total
		response = requests.post(url,json=body,headers=headers)
		response.encoding = "utf-8" 
		r = response.text
		if r is not None:
			if count > 1:
				r = json.loads(r)["patents"]
				r_all = r_all + r
			else: 
				r_all = json.loads(r)["patents"]
		count = count + 1
	# print (r_all)
	print (" Start filtering out patents with insufficient info and redundant inventors... ")
	filter_inventor(r_all)
	print (" Filtering is done.")
	print (" Start adding distance property into the dictionary of each patent.")
	add_distance(r_all) 
	print (" Adding distance is done.")  
	print(r_all[0])
	with open('results2.csv', 'w') as f:
	    JsonToCSV = csv.writer(f)
	    JsonToCSV.writerow(["patent_id","patent_title","patent_date","patent_kind", "inventor_distance", \
	    	"citation_times"])
	    #--Loop thru Each Object or Collection in JSON file
	    for item in r_all:
	    	JsonToCSV.writerow([item["patent_id"],
	    		item["patent_title"],
	    		item["patent_date"],
	    		item["patent_kind"],
	    		item["distance"],
	    		item["citation_times"]])
	time_end=time.time()
	print('Data fetching time',changeTime(time_end-time_start))