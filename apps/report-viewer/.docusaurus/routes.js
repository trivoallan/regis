import React from "react";
import ComponentCreator from "@docusaurus/ComponentCreator";

export default [
  {
    path: "/testing-base-url/",
    component: ComponentCreator("/testing-base-url/", "fb7"),
    routes: [
      {
        path: "/testing-base-url/",
        component: ComponentCreator("/testing-base-url/", "2da"),
        routes: [
          {
            path: "/testing-base-url/",
            component: ComponentCreator("/testing-base-url/", "ea2"),
            routes: [
              {
                path: "/testing-base-url/playbook",
                component: ComponentCreator(
                  "/testing-base-url/playbook",
                  "4f1",
                ),
                exact: true,
                sidebar: "defaultSidebar",
              },
              {
                path: "/testing-base-url/rules",
                component: ComponentCreator("/testing-base-url/rules", "e3c"),
                exact: true,
                sidebar: "defaultSidebar",
              },
              {
                path: "/testing-base-url/",
                component: ComponentCreator("/testing-base-url/", "954"),
                exact: true,
                sidebar: "defaultSidebar",
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    component: ComponentCreator("*"),
  },
];
