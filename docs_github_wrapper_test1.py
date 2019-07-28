from docs_github_wrapper import *

# Please create a Personal Access Token in GitHub
# https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

patoken = "ABCD1234"

###### Driver Code

public_repo = "azure-docs"
private_repo = "azure-docs-pr"
svc = "cosmos-db/svc"
begin_date = "2019-06-01"
end_date = "2019-07-01"

svc_public_prs = get_label_query(svc,public_repo,begin_date,end_date)
svc_private_prs = get_label_query(svc,private_repo,begin_date,end_date)

private_pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([svc_private_prs],patoken))
public_pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([svc_public_prs],patoken))

all_pr_data = get_pr_data_v4(private_pr_numbers_in_range, patoken, private_repo)
all_pr_data += get_pr_data_v4(public_pr_numbers_in_range, patoken, public_repo)

html_table(aggregate_sort_pr_data(all_pr_data,description_field='title'))
