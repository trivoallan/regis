"use strict";
(globalThis.webpackChunk_regis_dashboard =
  globalThis.webpackChunk_regis_dashboard || []).push([
  [4061],
  {
    4743(e, s, l) {
      (l.r(s), l.d(s, { default: () => o }));
      var r = l(10162),
        n = l(21016),
        a = l(25821),
        i = l(56730);
      const t = { opened: "emerald", merged: "blue", closed: "red" };
      function c() {
        const [e, s] = (0, r.useState)([]),
          [l, n] = (0, r.useState)(!0),
          [c, d] = (0, r.useState)(null),
          [h, x] = (0, r.useState)("opened");
        return (
          (0, r.useEffect)(() => {
            (n(!0),
              d(null),
              fetch(`/api/gitlab/mrs?state=${h}`)
                .then((e) => {
                  if (!e.ok) throw new Error(`HTTP ${e.status}`);
                  return e.json();
                })
                .then((e) => s(e.merge_requests ?? []))
                .catch((e) => d(e.message))
                .finally(() => n(!1)));
          }, [h]),
          c
            ? (0, i.jsxs)(a.Zp, {
                className: "mt-4",
                children: [
                  (0, i.jsxs)(a.EY, {
                    className: "text-red-500",
                    children: ["Failed to load merge requests: ", c],
                  }),
                  (0, i.jsxs)(a.EY, {
                    className: "mt-2",
                    children: [
                      "Make sure the server was started with ",
                      (0, i.jsx)("code", { children: "--gitlab-url" }),
                      ",",
                      " ",
                      (0, i.jsx)("code", { children: "--gitlab-token" }),
                      ", and ",
                      (0, i.jsx)("code", { children: "--gitlab-project" }),
                      ".",
                    ],
                  }),
                ],
              })
            : (0, i.jsxs)("div", {
                className: "mt-4",
                children: [
                  (0, i.jsxs)("div", {
                    className: "flex items-center gap-4 mb-4",
                    children: [
                      (0, i.jsx)(a.hE, { children: "Merge Requests" }),
                      (0, i.jsxs)(a.l6, {
                        value: h,
                        onValueChange: x,
                        className: "max-w-xs",
                        children: [
                          (0, i.jsx)(a.eb, {
                            value: "opened",
                            children: "Open",
                          }),
                          (0, i.jsx)(a.eb, {
                            value: "merged",
                            children: "Merged",
                          }),
                          (0, i.jsx)(a.eb, {
                            value: "closed",
                            children: "Closed",
                          }),
                          (0, i.jsx)(a.eb, { value: "all", children: "All" }),
                        ],
                      }),
                    ],
                  }),
                  (0, i.jsx)(a.Zp, {
                    children: (0, i.jsxs)(a.XI, {
                      children: [
                        (0, i.jsx)(a.nd, {
                          children: (0, i.jsxs)(a.Hj, {
                            children: [
                              (0, i.jsx)(a.M_, { children: "MR" }),
                              (0, i.jsx)(a.M_, { children: "Title" }),
                              (0, i.jsx)(a.M_, { children: "Author" }),
                              (0, i.jsx)(a.M_, { children: "State" }),
                              (0, i.jsx)(a.M_, { children: "Regis Labels" }),
                              (0, i.jsx)(a.M_, { children: "Report" }),
                              (0, i.jsx)(a.M_, { children: "Updated" }),
                            ],
                          }),
                        }),
                        (0, i.jsx)(a.BF, {
                          children: l
                            ? (0, i.jsx)(a.Hj, {
                                children: (0, i.jsx)(a.nA, {
                                  colSpan: 7,
                                  children: (0, i.jsx)(a.EY, {
                                    className: "text-center",
                                    children: "Loading...",
                                  }),
                                }),
                              })
                            : 0 === e.length
                              ? (0, i.jsx)(a.Hj, {
                                  children: (0, i.jsx)(a.nA, {
                                    colSpan: 7,
                                    children: (0, i.jsx)(a.EY, {
                                      className: "text-center",
                                      children: "No merge requests found.",
                                    }),
                                  }),
                                })
                              : e.map((e) =>
                                  (0, i.jsxs)(
                                    a.Hj,
                                    {
                                      children: [
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsxs)("a", {
                                            href: e.web_url,
                                            target: "_blank",
                                            rel: "noopener noreferrer",
                                            children: ["!", e.iid],
                                          }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsx)(a.EY, {
                                            className: "font-medium",
                                            children: e.title,
                                          }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsx)(a.EY, {
                                            children: e.author ?? "\u2014",
                                          }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsx)(a.Ex, {
                                            color: t[e.state] ?? "gray",
                                            children: e.state,
                                          }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsx)("div", {
                                            className: "flex flex-wrap gap-1",
                                            children:
                                              e.regis_labels.length > 0
                                                ? e.regis_labels.map((e) =>
                                                    (0, i.jsx)(
                                                      a.Ex,
                                                      {
                                                        size: "xs",
                                                        children: e.replace(
                                                          "regis::",
                                                          "",
                                                        ),
                                                      },
                                                      e,
                                                    ),
                                                  )
                                                : "\u2014",
                                          }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: e.has_report
                                            ? (0, i.jsx)(a.Ex, {
                                                color: "emerald",
                                                size: "xs",
                                                children: "Available",
                                              })
                                            : (0, i.jsx)(a.EY, {
                                                children: "\u2014",
                                              }),
                                        }),
                                        (0, i.jsx)(a.nA, {
                                          children: (0, i.jsx)(a.EY, {
                                            children: new Date(
                                              e.updated_at,
                                            ).toLocaleDateString(),
                                          }),
                                        }),
                                      ],
                                    },
                                    e.iid,
                                  ),
                                ),
                        }),
                      ],
                    }),
                  }),
                ],
              })
        );
      }
      function d() {
        const [e, s] = (0, r.useState)(""),
          [l, n] = (0, r.useState)("main"),
          [t, c] = (0, r.useState)(!1),
          [d, h] = (0, r.useState)(null),
          [x, o] = (0, r.useState)(null);
        return (0, i.jsxs)("div", {
          className: "mt-4",
          style: { maxWidth: 600 },
          children: [
            (0, i.jsx)(a.hE, { children: "Trigger Analysis" }),
            (0, i.jsx)(a.EY, {
              className: "mb-4",
              children: "Start a GitLab pipeline to analyze a container image.",
            }),
            (0, i.jsx)(a.Zp, {
              children: (0, i.jsxs)("form", {
                onSubmit: async function (s) {
                  if ((s.preventDefault(), e.trim())) {
                    (c(!0), o(null), h(null));
                    try {
                      const s = await fetch("/api/gitlab/trigger", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ image_url: e, ref: l }),
                      });
                      if (!s.ok) {
                        const e = await s.json().catch(() => ({}));
                        throw new Error(e.detail ?? `HTTP ${s.status}`);
                      }
                      h(await s.json());
                    } catch (s) {
                      o(s.message);
                    } finally {
                      c(!1);
                    }
                  }
                },
                className: "flex flex-col gap-4",
                children: [
                  (0, i.jsxs)("div", {
                    children: [
                      (0, i.jsx)("label", {
                        className: "block text-sm font-medium mb-1",
                        children: "Image URL",
                      }),
                      (0, i.jsx)(a.ks, {
                        placeholder:
                          "e.g. alpine:latest, nginx:1.25, ghcr.io/org/app:v2",
                        value: e,
                        onValueChange: s,
                      }),
                    ],
                  }),
                  (0, i.jsxs)("div", {
                    children: [
                      (0, i.jsx)("label", {
                        className: "block text-sm font-medium mb-1",
                        children: "Branch (ref)",
                      }),
                      (0, i.jsx)(a.ks, {
                        placeholder: "main",
                        value: l,
                        onValueChange: n,
                      }),
                    ],
                  }),
                  (0, i.jsx)(a.$n, {
                    type: "submit",
                    loading: t,
                    disabled: !e.trim() || t,
                    children: t ? "Triggering..." : "Run Analysis",
                  }),
                ],
              }),
            }),
            d &&
              (0, i.jsxs)(a.Zp, {
                className: "mt-4",
                children: [
                  (0, i.jsx)(a.EY, {
                    className: "font-medium text-emerald-600",
                    children: "Pipeline triggered successfully",
                  }),
                  (0, i.jsxs)("div", {
                    className: "mt-2 flex flex-col gap-1",
                    children: [
                      (0, i.jsxs)(a.EY, {
                        children: [
                          "Pipeline ID: ",
                          (0, i.jsxs)("strong", {
                            children: ["#", d.pipeline_id],
                          }),
                        ],
                      }),
                      (0, i.jsxs)(a.EY, {
                        children: [
                          "Status: ",
                          (0, i.jsx)("strong", { children: d.status }),
                        ],
                      }),
                      (0, i.jsx)("a", {
                        href: d.web_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        className: "text-blue-600 hover:underline",
                        children: "View pipeline on GitLab",
                      }),
                    ],
                  }),
                ],
              }),
            x &&
              (0, i.jsxs)(a.Zp, {
                className: "mt-4",
                children: [
                  (0, i.jsxs)(a.EY, {
                    className: "text-red-500",
                    children: ["Failed to trigger: ", x],
                  }),
                  (0, i.jsx)(a.EY, {
                    className: "mt-2",
                    children:
                      "Make sure the server was started with GitLab options and the token has pipeline trigger permissions.",
                  }),
                ],
              }),
          ],
        });
      }
      function h({ mr: e }) {
        return (0, i.jsxs)(a.Zp, {
          children: [
            (0, i.jsxs)("div", {
              className: "flex items-center gap-2 mb-2",
              children: [
                (0, i.jsx)(a.hE, {
                  children: (0, i.jsxs)("a", {
                    href: e.web_url,
                    target: "_blank",
                    rel: "noopener noreferrer",
                    children: ["!", e.iid],
                  }),
                }),
                (0, i.jsx)(a.Ex, {
                  color: "opened" === e.state ? "emerald" : "blue",
                  children: e.state,
                }),
              ],
            }),
            (0, i.jsx)(a.EY, {
              className: "font-medium mb-3",
              children: e.title,
            }),
            (0, i.jsxs)("div", {
              className: "flex flex-col gap-2",
              children: [
                (0, i.jsxs)("div", {
                  children: [
                    (0, i.jsx)(a.EY, {
                      className: "text-xs font-medium uppercase",
                      children: "Regis Labels",
                    }),
                    (0, i.jsx)("div", {
                      className: "flex flex-wrap gap-1 mt-1",
                      children:
                        e.regis_labels.length > 0
                          ? e.regis_labels.map((e) =>
                              (0, i.jsx)(
                                a.Ex,
                                {
                                  size: "xs",
                                  children: e.replace("regis::", ""),
                                },
                                e,
                              ),
                            )
                          : (0, i.jsx)(a.EY, { children: "None" }),
                    }),
                  ],
                }),
                (0, i.jsxs)("div", {
                  children: [
                    (0, i.jsx)(a.EY, {
                      className: "text-xs font-medium uppercase",
                      children: "Report",
                    }),
                    (0, i.jsx)(a.EY, {
                      children: e.has_report
                        ? (0, i.jsx)(a.Ex, {
                            color: "emerald",
                            size: "xs",
                            children: "Available",
                          })
                        : "Not available",
                    }),
                  ],
                }),
                e.pipeline &&
                  (0, i.jsxs)("div", {
                    children: [
                      (0, i.jsx)(a.EY, {
                        className: "text-xs font-medium uppercase",
                        children: "Pipeline",
                      }),
                      (0, i.jsxs)("div", {
                        className: "flex items-center gap-2",
                        children: [
                          (0, i.jsx)(a.Ex, {
                            color:
                              "success" === e.pipeline.status
                                ? "emerald"
                                : "yellow",
                            size: "xs",
                            children: e.pipeline.status,
                          }),
                          (0, i.jsxs)("a", {
                            href: e.pipeline.web_url,
                            target: "_blank",
                            rel: "noopener noreferrer",
                            className: "text-xs text-blue-600 hover:underline",
                            children: ["#", e.pipeline.id],
                          }),
                        ],
                      }),
                    ],
                  }),
              ],
            }),
          ],
        });
      }
      function x() {
        const [e, s] = (0, r.useState)(""),
          [l, n] = (0, r.useState)(""),
          [t, c] = (0, r.useState)(null),
          [d, x] = (0, r.useState)(null),
          [o, m] = (0, r.useState)(!1),
          [j, u] = (0, r.useState)(null);
        async function p(e) {
          const s = await fetch(`/api/gitlab/mrs/${e}`);
          if (!s.ok) {
            const l = await s.json().catch(() => ({}));
            throw new Error(l.detail ?? `MR !${e}: HTTP ${s.status}`);
          }
          return s.json();
        }
        return (0, i.jsxs)("div", {
          className: "mt-4",
          children: [
            (0, i.jsx)(a.hE, { children: "Compare Merge Requests" }),
            (0, i.jsx)(a.EY, {
              className: "mb-4",
              children:
                "Enter two MR IIDs to compare their analysis results side by side.",
            }),
            (0, i.jsxs)("div", {
              className: "flex items-end gap-4 mb-6",
              children: [
                (0, i.jsxs)("div", {
                  children: [
                    (0, i.jsx)("label", {
                      className: "block text-sm font-medium mb-1",
                      children: "Left MR",
                    }),
                    (0, i.jsx)(a.ks, {
                      placeholder: "e.g. 42",
                      value: e,
                      onValueChange: s,
                    }),
                  ],
                }),
                (0, i.jsxs)("div", {
                  children: [
                    (0, i.jsx)("label", {
                      className: "block text-sm font-medium mb-1",
                      children: "Right MR",
                    }),
                    (0, i.jsx)(a.ks, {
                      placeholder: "e.g. 43",
                      value: l,
                      onValueChange: n,
                    }),
                  ],
                }),
                (0, i.jsx)(a.$n, {
                  onClick: async function () {
                    if (e.trim() && l.trim()) {
                      (m(!0), u(null), c(null), x(null));
                      try {
                        const [s, r] = await Promise.all([p(e), p(l)]);
                        (c(s), x(r));
                      } catch (s) {
                        u(s.message);
                      } finally {
                        m(!1);
                      }
                    }
                  },
                  loading: o,
                  disabled: !e.trim() || !l.trim() || o,
                  children: "Compare",
                }),
              ],
            }),
            j &&
              (0, i.jsx)(a.Zp, {
                className: "mb-4",
                children: (0, i.jsx)(a.EY, {
                  className: "text-red-500",
                  children: j,
                }),
              }),
            t &&
              d &&
              (0, i.jsxs)(a.xA, {
                numItems: 1,
                numItemsMd: 2,
                className: "gap-4",
                children: [(0, i.jsx)(h, { mr: t }), (0, i.jsx)(h, { mr: d })],
              }),
          ],
        });
      }
      function o() {
        return (0, i.jsx)(n.A, {
          title: "GitLab Integration",
          children: (0, i.jsxs)("div", {
            className: "container margin-top--lg margin-bottom--lg",
            children: [
              (0, i.jsx)("h1", { children: "GitLab Integration" }),
              (0, i.jsxs)(a.fu, {
                children: [
                  (0, i.jsxs)(a.wb, {
                    children: [
                      (0, i.jsx)(a.oz, { children: "Merge Requests" }),
                      (0, i.jsx)(a.oz, { children: "Trigger Analysis" }),
                      (0, i.jsx)(a.oz, { children: "Compare" }),
                    ],
                  }),
                  (0, i.jsxs)(a.T2, {
                    children: [
                      (0, i.jsx)(a.Kp, { children: (0, i.jsx)(c, {}) }),
                      (0, i.jsx)(a.Kp, { children: (0, i.jsx)(d, {}) }),
                      (0, i.jsx)(a.Kp, { children: (0, i.jsx)(x, {}) }),
                    ],
                  }),
                ],
              }),
            ],
          }),
        });
      }
    },
  },
]);
