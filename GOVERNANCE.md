# Abstract

This Project is consensus-based and belongs in the *NiPreps (NeuroImaging PREProcessing toolS)* Community.
Anyone with an interest in the Project can join the Community, contribute to the Project design, and participate in the decision making process. This document describes how that participation takes place, how to find consensus, and how deadlocks are resolved.

# Governance Policy

This document provides the governance policy for the Project.
In general, all *NiPreps Projects* embrace a [liberal contribution model](https://opensource.guide/leadership-and-governance/#what-are-some-of-the-common-governance-structures-for-open-source-projects) of governance structure.
However, because of the scientific domain of NiPreps , the community features some structure from *meritocracy models* to prescribe [the order in the authors list of new papers](https://www.nipreps.org/community/CONTRIBUTING/#publications) about these tools.

## 1. Roles.

This project may include the following roles. Additional roles may be adopted and documented by the Project.

**1.1. Maintainers**.
Maintainers are members of a wonderful team *driving the Project* and thereby are responsible for organizing activities around developing, maintaining, and updating the Project.
Other examples of activities that drive the Project are: actively participating in the follow-up meetings, leading documentation sprints, helping in the design of the tool and definition of the roadmap, providing resources (in the broad sense, including funding), code-review, etc.
Maintainers are also responsible for determining consensus.
This Project may add or remove Maintainers with the approval of the current Maintainers.
Maintainers agree to this policy and to abide by all Project polices, including the code of conduct, trademark policy, and antitrust policy by adding their name to the `.maint/MAINTAINERS.md` file.

**1.2. Contributors**. Contributors are those who actively help or have previously helped the Project in a broad sense.
Any community member can become a contributor by interacting directly with the project in concrete ways, such as:

* proposing new features, changes to the code or documentation improvements via a GitHub pull request;
* contributing with benchmarking modules of the tool;
* reporting issues on our GitHub issues page;
* helping improve the scientific rigor of implementations;
* giving out support on the different communication channels (mattermost, NeuroStars , GitHub, etc.);
* discussing the design of the library, website, or tutorials on the mailing list, or in existing issues and pull requests; or
* reviewing open pull requests;

among other possibilities.
By contributing to the project, community members can directly help to shape its future.

Contributors should read the [*NiPreps Community's guidelines*](https://www.nipreps.org/community/), which contain a [code of conduct](https://www.nipreps.org/community/CODE_OF_CONDUCT/), [contributing guidelines](https://www.nipreps.org/community/CONTRIBUTING/), and [criteria for accepting new features](https://www.nipreps.org/community/features/), amongst other relevant documents.
Contributors agree to this policy and to abide by all Project polices by adding their name to the `.maint/CONTRIBUTORS.md` file.

**1.3. Principal investigators**.
PIs are those who provide or have provided institutional resources (personnel, funding, etc.) to the Project, and play a supervision role over the development of the Project.
PIs have reserved the last position as senior authors of papers and other dissemination activities.
This Project may add or remove PIs with the approval of the Organization Steering Committee.
PIs enlisted in the `.maint/PIs.md` file agree to this policy and to abide by all Project polices.

**1.4. Former members**.
Those who have contributed at some point to the Project but were required or they wished to disconnect from the Project's updates and to drop-out from publications and other dissemination activities, are listed in the `.maint/FORMER.md` file.

## 2. Decisions.

**2.1. Consensus-Based Decision Making**.
Projects make decisions through consensus of the Maintainers.
While explicit agreement of all Maintainers is preferred, it is not required for consensus.
Rather, the Maintainers will determine consensus based on their good faith consideration of a number of factors, including the dominant view of the Contributors and nature of support and objections.
The Maintainers will document evidence of consensus in accordance with these requirements.

**2.2. Appeal Process**. Decisions may be appealed by opening an issue and that appeal will be considered by the Maintainers in good faith, who will respond in writing within a reasonable time. If the Maintainers deny the appeal, the appeal my be brought before the Organization Steering Committee, who will also respond in writing in a reasonable time.

## 3. How We Work.

**3.1. Openness**. Participation is open to anyone who is directly and materially affected by the activity in question. There shall be no undue financial barriers to participation.

**3.2. Balance**. The development process should balance the interests of Contributors and other stakeholders. Contributors from diverse interest categories shall be sought with the objective of achieving balance.

**3.3. Coordination and Harmonization**. Good faith efforts shall be made to resolve potential conflicts or incompatibility between releases in this Project.

**3.4. Consideration of Views and Objections**. Prompt consideration shall be given to the written views and objections of all Contributors.

**3.5. Written procedures**. This governance document and other materials documenting this project's development process shall be available to any interested person.

**3.6. Community roadmap and release planning**.
Maintainers shall keep open planification documents and roadmap definition and maintenance, and are responsible to seek feedback and engage contributors in the process of defining the future lines of the Project.
Principal investigators will inform Maintainers about the existing commitments with funding agencies and other relevant institutions in terms of deliverables and milestones that the Project might need to observe to respond to such commitments.
In case of conflict between the Maintainers' criteria and the Principal investigators' proposal, an appeal must be addressed to the Organization Steering Committee.
The Project may maintain a `.maint/ROADMAP.md` stating how roadmaps are built, how issues are prioritized and organized, and the how the release process and achievement of deliverables and milestones are monitored.

## 4. Release process and Scientific publication.

### 4.1. Releases

This Project follows the *NiPreps Community* guidelines for [releases](https://www.nipreps.org/devs/releases/) and [version synchrony](https://www.nipreps.org/devs/versions/).
The release process may be initiated by any Maintainer, who will follow the prescribed documentation to the effect.
This project has an automated deployment pipeline triggered with a git tagging operation by a Maintainer, which ensures the minting of the correct version number, python and docker packaging, publication of packages in open repositories and finally, the posting of a new release entry at Zenodo.

**Long-term support (LTS) release series**.
End-user applications may commit to extended windows of support for particular version series (see [related documentation here](https://www.nipreps.org/devs/releases/#long-term-support-series)).
Past release series are maintained with *maintenance* branches named `maint/<YY>.<minor>.x` (for instance fMRIPrep's `maint/20.2.x`).
For those maintenance branches tagged as LTS series, the `.maint/MAINTAINERS.md` and the `.maint/PIs.md` may differ from those of the development (called `master` or `main`) branch.
New contributors to a maintenance branch will be added to the `.maint/CONTRIBUTORS.md` file of that branch, and then upstreamed to posterior `maint/<series>` branches and the `master`/`main` branch of the repository.

### 4.2. Posting releases on Zenodo

In the absence of higher-priority scientific publications, the appropriate Zenodo entry should be cited when referencing the Project.
Metadata submitted to the Zenodo repository is contained in the `/.zenodo.json` file at the root of the Project repository.
Before every new release, the metadata containing the authors and contributors of the Project must be updated running `python .maint/update_authors.py zenodo` from the root of the repository, on the appropriate release branch.

### 4.3. Scientific publication

Anyone listed as a Maintainer or a Contributor is invited to prepare and submit manuscript to journals as first author.
To compose the author list, all the Maintainers of the Project MUST be included and notified; and all the Contributors MUST be invited to participate.
First authorship(s) is (are) reserved for the authors that originated and kept the initiative of submission and wrote the manuscript.
Finally Principal Investigators are appended to the end of the author's list.

To generate the ordering of your paper, please run `python .maint/update_authors.py publication` from the root of the repository, on the up-to-date upstream/master branch (or the appropriate tag this publication is based off).
Then, please modify this list and place your name first.

**Public announcement**.
Publishing initiatives must be properly publicized through appropriate channels (GitHub discussions, NiPy Discourse, email lists, etc.) and made with sufficient anticipation for the Community to take corrective measures.

**Open science pledge**.
*NiPreps* and its community adheres to open science principles, such that a pre-print should be posted on an adequate archive service (e.g., ArXiv or BioRxiv) prior publication.

**Disagreement**.
In the case that any member of the community objects to the initiative of submitting a paper derived from the Project or its activities, or objects to the tentative individuals and/or their ordering in the author's list, the Principal Investigators of the project will determine a solution in coordination with the Maintainers.
If such a solution would not be acceptable by all the affected parties, an appeal may be addressed to the Organization's Steering Committee, which will reach out to the Principal Investigators to fully understand the conflict and establish the ultimate solution.

## 5. No Confidentiality.

Information disclosed in connection with any Project activity, including but not limited to meetings, contributions, and submissions, is not confidential, regardless of any markings or statements to the contrary.

## 6. Trademarks.

Any names, trademarks, logos, or goodwill developed by and associated with the Project (the "Marks") are controlled by the Organization. Maintainers may only use these Marks in accordance with the Organization's trademark policy. If a Maintainer resigns or is removed, any rights the Maintainer may have in the Marks revert to the Organization.

## 7. Amendments.

Amendments to this governance policy may be made by affirmative vote of 2/3 of all Maintainers, with approval by the Organization's Steering Committee.

---
Part of MVG-0.1-beta.
Made with love by GitHub. Licensed under the [CC-BY 4.0 License](https://creativecommons.org/licenses/by-sa/4.0/).
