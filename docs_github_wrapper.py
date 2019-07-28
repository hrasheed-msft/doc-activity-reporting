import requests
import json
from lxml import html
import datetime

def call_github_api_iter(api_urls, patoken):
    
    headers1 = {'Authorization': 'token ' + patoken, 'Accept': 'application/vnd.github.symmetra-preview+json'}
    json_data_array = []
    
    for api_url in api_urls:  
    
        current_response = requests.get(url=api_url, headers=headers1)

        json_data_array.append(current_response.json())

        if len(json_data_array) > 10:
            return (json_data_array)

        while 'next' in current_response.links.keys():
            current_response = requests.get(url=current_response.links['next']['url'], headers=headers1)
            json_data_array.append(current_response.json())
    
    return (json_data_array)
    
def extract_pr_numbers(json_response_array):
    pr_list = []
    for json_response in json_response_array:  
        json_obj = json.loads(json.dumps(json_response))
        for pr in json_obj['items']:
            number = json.dumps(pr['number'])
            #title = json.dumps(pr['title'])
            pr_list.append(number)        
    return(pr_list)
    
def get_pr_data_v4(pr_number_array, patoken, repo):

    url = 'https://api.github.com/graphql' 
    headers = {'Authorization': 'token ' + patoken}
    
    all_pr_data = []
    
    for pr_number in pr_number_array:
        pr_files_query = """{repository(owner:"MicrosoftDocs", name: "%s") {
            pullRequest(number: %d){
                author{login}
                url
                title
                bodyText
                createdAt
                additions
                changedFiles
                state
                publishedAt
                number
                commits(first: 10)
                {
                edges{
                  node{
                    id
                    commit
                    {
                      changedFiles
                    }
                  }
                }
                }
                files(last: 100){
                edges{
                  node{
                    path
                    additions
                    deletions
                  }
                }
                }
            }
          }
        }
        """ % (repo, int(pr_number))
        json1 = {'query' : '%s' % pr_files_query}
        r = requests.post(url=url, json=json1, headers=headers)
        json_string = r.json()        
        all_pr_data.append(json_string)
    
    return(all_pr_data)
    
def aggregate_sort_pr_data(pr_data_array,description_field='title'):
    file_info = {}
    file_info_list = []
    
    for pr in pr_data_array:
        pr_url = json.dumps(pr['data']['repository']['pullRequest']['url'])
        number = json.dumps(pr['data']['repository']['pullRequest']['number'])
        author = json.dumps(pr['data']['repository']['pullRequest']['author']['login'])
        published_date = json.dumps(pr['data']['repository']['pullRequest']['publishedAt'])
        
        title = json.dumps(pr['data']['repository']['pullRequest']['title'])
        bodyText = json.dumps(pr['data']['repository']['pullRequest']['bodyText'])
               
        for file in pr['data']['repository']['pullRequest']['files']['edges']:
            file_name = json.dumps(file['node']['path']).replace("\"","")
            
            if ".md" not in file_name:
                continue
            
            pr_additions = json.dumps(file['node']['additions'])
            pr_deletions = json.dumps(file['node']['deletions'])

            current_file_info = file_info.get(file_name,{})
            current_file_info["total_modifications"] = current_file_info.get("total_modifications",0) + int(pr_additions) + int(pr_deletions)
            current_file_info["times_modified"] = current_file_info.get("times_modified",0) + 1
            
            
            if description_field == "title":
                if len(title) > 2:
                        if 'description' in current_file_info:
                            current_file_info["description"] = str(current_file_info.get("description","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
                        else:
                            current_file_info["description"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
            else:
                if len(bodyText) > 2:
                    if 'description' in current_file_info:
                        current_file_info["description"] = str(current_file_info.get("description","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
                    else:
                        current_file_info["description"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
            

            file_info[file_name] = current_file_info
    
    for key in file_info.keys():
        
        if "description" not in file_info[key]:
            file_info[key]["description"] = "None"
            
        file_info_list.append({"file_name": key,
                               "total_modifications": file_info[key]["total_modifications"],
                               "times_modified":file_info[key]["times_modified"],
                               "description":file_info[key]["description"]})
    
    sorted_list = sorted(file_info_list, key=lambda k: k['total_modifications'], reverse=True) 
    return sorted_list  
    
def html_table(list_of_dicts):
    final_string = '''
    <html>
        <head>
            <style type="text/css">
            #docupdates {
              font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
              border-collapse: collapse;
              width: 100%;
            }

            #docupdates td, #docupdates th {
              border: 1px solid #ddd;
              padding: 8px;
            }

            #docupdates tr:nth-child(even){background-color: #f2f2f2;}

            #docupdates tr:hover {background-color: #ddd;}

            #docupdates th {
              padding-top: 12px;
              padding-bottom: 12px;
              text-align: left;
              background-color: #000000;
              color: white;
            }
            </style>
        </head>
    '''
    final_string += '<table id="docupdates">'
    final_string += '<tr><th>Doc Title</th><th>Total Lines Modified</th><th>Number of Pull Requests</th><th>Description of Changes</th></tr>'
    for file_dict in list_of_dicts:
        if len(file_dict)>0:
            final_string += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(output_docs_link(file_dict["file_name"]),file_dict["total_modifications"],file_dict["times_modified"],file_dict["description"])
    final_string += '</table></html>'
    cur_dt1 = datetime.datetime.today()
    dt_str = '{:%m_%d_%y_%H_%M}'.format(cur_dt1)
    file_name = "GitHub_PR_Query_Data_"+dt_str+".html"
    with open(file_name, "w") as text_file:
        print(final_string, file=text_file)
        
def output_docs_link(file_path):
    shortened_path = file_path[file_path.find("articles/")+9:file_path.find(".md")]
    url = "https://docs.microsoft.com/en-us/azure/"+shortened_path
    return('<a href="{}">{}</a>'.format(url, get_doc_title(url)))
    
def get_doc_title(url):
    page = requests.get(url, allow_redirects=False)
    if page.status_code == requests.codes.ok:
        tree = html.fromstring(page.content)
        doc_title = tree.xpath('//h1/text()')
        return doc_title[0].replace("'","")
    elif page.status_code == requests.codes.moved_permanently:
        doc_title = "[PERMANENTLY REDIRECTING] " + url
        return doc_title
    elif page.status_code == requests.codes.not_found:
        doc_title = "[PERMANENTLY REDIRECTING] " + url
        return doc_title        
    
def get_author_query(author, repo, begin_date, end_date):
    author_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr author:{} is:merged merged:{}..{}'.format(repo, author, begin_date, end_date)
    return author_prs
    
def get_label_query(svc_label, repo, begin_date, end_date):
    svc_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr label:{} is:merged merged:{}..{}'.format(repo, svc_label, begin_date, end_date)
    return svc_prs
