#########################################################################################
# File Name: docs_github_wrapper_test2.py
# Date: 07/28/2019
# Author: Hassan Rasheed
# Description: Test code for the docs GitHub wrapper. This test uses author query
#               along with a service query.
#########################################################################################

from docs_github_wrapper import *

# Please create a Personal Access Token in GitHub
# https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

patoken = "ABCDEFG123456789"

###### Driver Code

public_repo = "azure-docs"
private_repo = "azure-docs-pr"
author = "hrasheed-msft"
svc = "hdinsight/svc"
begin_date = "2019-07-01"
end_date = "2019-07-25"

author_private_prs = get_author_query(author,private_repo,begin_date,end_date)

svc_public_prs = get_label_query(svc,public_repo,begin_date,end_date)

pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([author_private_prs],patoken))
public_pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([svc_public_prs],patoken))

# Note: if you have multiple lists of prs that use the same repository they can be included in the same call to get_pr_data_v4
all_pr_data = get_pr_data_v4(pr_numbers_in_range, patoken, private_repo)
all_pr_data += get_pr_data_v4(public_pr_numbers_in_range, patoken, public_repo)

html_table(aggregate_sort_pr_data(all_pr_data,description_field='bodyText'))
