#!/usr/bin/env python
import sys
from boto3 import Session

if __name__ == "__main__":
    if len(sys.argv) > 1:
        subject = sys.argv[1]

        session = Session()
        credentials = session.get_credentials()
        # Credentials are refreshable, so accessing your access key / secret key
        # separately can lead to a race condition. Use this to get an actual matched
        # set.
        current_credentials = credentials.get_frozen_credentials()

        access_key = current_credentials.access_key
        secret_key = current_credentials.secret_key

        with open("run_dmriprep.yml.tmpl", 'r') as template:
            with open("jobs/job_{}.yml".format(subject), 'w') as f:
                all_text = "\n".join(template.readlines())
                all_text = all_text.replace("{{subject}}", subject)
                all_text = all_text.replace("{{access_key}}", access_key)
                all_text = all_text.replace("{{secret_key}}", secret_key)
                f.write(all_text)

