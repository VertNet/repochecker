# VertNet's Repository name checker

This repository contains the code for VertNet's repository name checker.

This tool is used to check the consistency of names between the project's registry tables and GitHub's repositories.

For deployment strategies, see https://github.com/VertNet/portal-web/wiki/Portal-development#deployment.

# Background

VertNet's registry tables store certain information about the resources of the publishers that build the network. Among others, the names of the GitHub organization and repository are stored for each resource (for feedback and monthly stats delivery purposes). However, since adding these is not an automated process and there is no update trigger in place, there can be mismatches between the registered name and the actual name of the organization and/or the repository. The task of this program is to detect such inconsistencies.

# How it works

By calling the URL below, one can fire off the process of checking the consistency of names.

> [http://tools-repochecker.vertnet-portal.appspot.com][repochecker]

It will first get the data from VertNet's registry and, for each record, keep the stored values for the GitHub organization and repository names. Then, for each of those name-pairs, it will shoot GitHub API calls to check for the existence of that combination. In case it misses, the pair is logged as failed.

When all names are checked, if there was any mismatch, VertNet administrators and dev team will receive an email with the failed names. Otherwise, the program will return a "success" message.

# Other project repositories

* VertNet web portal: [https://github.com/VertNet/portal-web][vn-portal]
* VertNet API: [https://github.com/VertNet/api][vn-api]
* Harvesting: [https://github.com/VertNet/gulo][vn-gulo]
* Indexing: [https://github.com/VertNet/dwc-indexer][dwc-indexer]
* Toolkit: [https://github.com/VertNet/toolkit][vn-toolkit]
* Georeferencing calculator: [https://github.com/VertNet/georefcalculator][georef-calc]
* Geospatial Quality API: [https://github.com/VertNet/api-geospatial][vn-geoapi]
* Usage Statistics Generation: [https://github.com/VertNet/usagestats][vn-usagestats]
* BigQuery: [https://github.com/VertNet/bigquery][vn-bigquery]

<!-- links -->
[vn-portal]: https://github.com/VertNet/portal-web
[vn-api]: https://github.com/VertNet/api
[vn-gulo]: https://github.com/VertNet/gulo
[dwc-indexer]: https://github.com/VertNet/dwc-indexer
[vn-toolkit]: https://github.com/VertNet/toolkit
[georef-calc]: https://github.com/VertNet/georefcalculator
[vn-geoapi]: https://github.com/VertNet/api-geospatial
[vn-usagestats]: https://github.com/VertNet/usagestats
[vn-bigquery]: https://github.com/VertNet/bigquery
[development]: https://github.com/VertNet/api/wiki/Development
[search-wiki]: https://github.com/VertNet/api/wiki/Search-API
[download-wiki]: https://github.com/VertNet/api/wiki/Download-API
[repochecker]: http://tools-repochecker.vertnet-portal.appspot.com
