# Atlassian Prep

Atlassian interview questions (GothamLoop question bank), one folder per problem. Each folder holds the problem writeup and a runnable study notebook side by side, so there's no jumping between locations to review one problem.

## Problems

| # | Problem | Notebook |
|---|---|---|
| 1 | [Jira Issue CSV Exporter](1.%20Jira_Issue_CSV_Exporter/README.md) | [notebook](1.%20Jira_Issue_CSV_Exporter/1.%20Jira_Issue_CSV_Exporter.ipynb) |
| 2 | [Confluence Page Word Count](2.%20Confluence_Page_Word_Count/README.md) | [notebook](2.%20Confluence_Page_Word_Count/2.%20Confluence_Page_Word_Count.ipynb) |
| 3 | [Content Popularity Tracker](3.%20Content_Popularity_Tracker/README.md) | [notebook](3.%20Content_Popularity_Tracker/3.%20Content_Popularity_Tracker.ipynb) |
| 4 | [Highest Price](4.%20Highest_Price/README.md) | [notebook](4.%20Highest_Price/4.%20Highest_Price.ipynb) |
| 5 | [Middleware Router](5.%20Middleware_Router/README.md) | [notebook](5.%20Middleware_Router/5.%20Middleware_Router.ipynb) |
| 6 | [Ballot Processing](6.%20Ballot_Processing/README.md) | [notebook](6.%20Ballot_Processing/6.%20Ballot_Processing.ipynb) |
| 7 | [CI/CD Jobs](7.%20CICD_Jobs/README.md) | [notebook](7.%20CICD_Jobs/7.%20CICD_Jobs.ipynb) |
| 8 | [Company Hierarchy](8.%20Company_Hierarchy/README.md) | [notebook](8.%20Company_Hierarchy/8.%20Company_Hierarchy.ipynb) |
| 9 | [Confluence Page Link Graph](9.%20Confluence_Page_Link_Graph/README.md) | [notebook](9.%20Confluence_Page_Link_Graph/9.%20Confluence_Page_Link_Graph.ipynb) |
| 10 | [Customer Satisfaction](10.%20Customer_Satisfaction/README.md) | [notebook](10.%20Customer_Satisfaction/10.%20Customer_Satisfaction.ipynb) |
| 11 | [Data Engineer Questions](11.%20Data_Engineer_Questions/README.md) | [notebook](11.%20Data_Engineer_Questions/11.%20Data_Engineer_Questions.ipynb) |
| 12 | [File System](12.%20File_System/README.md) | [notebook](12.%20File_System/12.%20File_System.ipynb) |
| 13 | [Tennis Club](13.%20Tennis_Club/README.md) | [notebook](13.%20Tennis_Club/13.%20Tennis_Club.ipynb) |

## Shape of each problem folder

```
<N>. <Problem_Name>/
├── README.md                    — the original problem writeup: statement, hints, official answer, walkthrough, talking points, follow-ups
└── <N>. <Problem_Name>.ipynb    — study notebook: concepts primers, solutions ordered worst -> optimal, verification, empirical complexity benchmark, patterns learned
```

`bench_utils.py` (shared benchmarking helper used by every notebook) stays at this folder's root — each notebook finds it by walking up from its own directory, so it works regardless of nesting depth.
