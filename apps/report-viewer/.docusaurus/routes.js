import React from "react";
import ComponentCreator from "@docusaurus/ComponentCreator";

export default [
  {
    path: "/",
    component: ComponentCreator("/", "a3d"),
    routes: [
      {
        path: "/",
        component: ComponentCreator("/", "1d3"),
        routes: [
          {
            path: "/",
            component: ComponentCreator("/", "1f0"),
            routes: [
              {
                path: "/playbook",
                component: ComponentCreator("/playbook", "8ae"),
                exact: true,
                sidebar: "defaultSidebar",
              },
              {
                path: "/rules",
                component: ComponentCreator("/rules", "f47"),
                exact: true,
                sidebar: "defaultSidebar",
              },
              {
                path: "/",
                component: ComponentCreator("/", "87e"),
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
