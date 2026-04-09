import React, { useState } from "react";
import Layout from "@theme/Layout";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@tremor/react";
import { GitLabMRList } from "@site/src/components/GitLabMRList";
import { TriggerAnalysis } from "@site/src/components/TriggerAnalysis";
import { MRComparison } from "@site/src/components/MRComparison";

export default function GitLabPage(): React.JSX.Element {
  return (
    <Layout title="GitLab Integration">
      <div className="container margin-top--lg margin-bottom--lg">
        <h1>GitLab Integration</h1>
        <TabGroup>
          <TabList>
            <Tab>Merge Requests</Tab>
            <Tab>Trigger Analysis</Tab>
            <Tab>Compare</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              <GitLabMRList />
            </TabPanel>
            <TabPanel>
              <TriggerAnalysis />
            </TabPanel>
            <TabPanel>
              <MRComparison />
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </div>
    </Layout>
  );
}
