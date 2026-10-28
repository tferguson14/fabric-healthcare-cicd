# Sources and attribution

The release pattern is based on Microsoft's [Fabric CI/CD Azure DevOps tutorial](https://learn.microsoft.com/en-us/fabric/cicd/tutorial-fabric-cicd-azure-devops), translated into original GitHub Actions workflows and Python lab scripts. Design discussion also references Microsoft's [Fabric CI/CD best practices](https://learn.microsoft.com/en-us/fabric/fundamentals/understand-best-practices-fabric-cicd).

The synthetic healthcare fixture comes from [SmartterHealth/FabricHackathon](https://github.com/SmartterHealth/FabricHackathon), commit `a84b0ff81d27c5da3b1fb8aac5641cd5507a78ac`. `sample-manifest.json` identifies the exact seven CSVs. The downloader retrieves them directly from that source, and verifies their hashes and record counts. Original source notebooks and medical background prose are not redistributed here. The four bootstrap notebooks are new lab implementations using the source CSV column names.

Retain attribution to the source repository. Public repository visibility alone is not a license grant; review the upstream repository's terms before redistributing its data or incorporating it into customer deliverables. This package does not grant rights to third-party material. Installed dependencies retain their own licenses.

Official technical documentation is linked in the lab guide's references. Package and action versions were inspected on October 28, 2026. Pin updates should be reviewed and tested before a demo.
