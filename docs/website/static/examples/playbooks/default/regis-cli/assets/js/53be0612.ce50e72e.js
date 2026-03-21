"use strict";
(globalThis.webpackChunk_regis_cli_report_viewer =
  globalThis.webpackChunk_regis_cli_report_viewer || []).push([
  [3375],
  {
    18819(e, r, s) {
      (s.r(r),
        s.d(r, {
          assets: () => b,
          contentTitle: () => j,
          default: () => k,
          frontMatter: () => x,
          metadata: () => t,
          toc: () => v,
        }));
      const t = JSON.parse(
        '{"id":"rules","title":"Rules","description":"","source":"@site/docs/rules.mdx","sourceDirName":".","slug":"/rules","permalink":"/rules","draft":false,"unlisted":false,"tags":[],"version":"current","frontMatter":{"title":"Rules","hide_title":true},"sidebar":"defaultSidebar","previous":{"title":"Summary","permalink":"/"},"next":{"title":"Dockle","permalink":"/analyzers/dockle"}}',
      );
      var l = s(56730),
        a = s(59336),
        n = s(10162),
        o = s(81450),
        i = s(17879),
        c = s(25821),
        d = s(21664);
      const u = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];
      function m(e) {
        const r = u.findIndex((r) => r.toLowerCase() === e?.toLowerCase());
        return -1 === r ? u.length : r;
      }
      function p({ passed: e, status: r }) {
        const s = { fontSize: "1.5rem" };
        return "incomplete" === r
          ? (0, l.jsx)("span", {
              title: "Incomplete",
              style: s,
              children: "\u26a0\ufe0f",
            })
          : e
            ? (0, l.jsx)("span", {
                title: "Passed",
                style: s,
                children: "\u2705",
              })
            : (0, l.jsx)("span", {
                title: "Failed",
                style: s,
                children: "\u274c",
              });
      }
      function f({ level: e, rules: r }) {
        const s = r.filter((e) => e.passed).length;
        return (0, l.jsxs)("div", {
          style: { marginBottom: "2rem" },
          children: [
            (0, l.jsxs)("div", {
              style: {
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                marginBottom: "0.75rem",
              },
              children: [
                (0, l.jsx)(d.M, { label: e, variant: (0, d.Z)(e) }),
                (0, l.jsxs)("small", {
                  style: { opacity: 0.6 },
                  children: [s, " / ", r.length, " passed"],
                }),
              ],
            }),
            (0, l.jsxs)(c.XI, {
              children: [
                (0, l.jsx)(c.nd, {
                  children: (0, l.jsxs)(c.Hj, {
                    children: [
                      (0, l.jsx)(c.M_, {
                        style: { width: "3rem" },
                        children: "Status",
                      }),
                      (0, l.jsx)(c.M_, { children: "Rule" }),
                    ],
                  }),
                }),
                (0, l.jsx)(c.BF, {
                  children: r.map((e, r) =>
                    (0, l.jsxs)(
                      c.Hj,
                      {
                        children: [
                          (0, l.jsx)(c.nA, {
                            style: { textAlign: "center" },
                            children: (0, l.jsx)(p, {
                              passed: e.passed,
                              status: e.status,
                            }),
                          }),
                          (0, l.jsxs)(c.nA, {
                            children: [
                              (0, l.jsx)("strong", {
                                children: e.description ?? e.title ?? e.slug,
                              }),
                              e.message &&
                                (0, l.jsx)("div", {
                                  style: {
                                    fontSize: "0.85rem",
                                    opacity: 0.8,
                                    marginTop: "0.2rem",
                                  },
                                  children: e.message,
                                }),
                              e.analyzers &&
                                e.analyzers.length > 0 &&
                                (0, l.jsx)("div", {
                                  style: {
                                    marginTop: "0.3rem",
                                    display: "flex",
                                    gap: "0.25rem",
                                    flexWrap: "wrap",
                                  },
                                  children: e.analyzers.map((e) =>
                                    (0, l.jsx)(
                                      i.A,
                                      {
                                        to: `/analyzers/${e}`,
                                        style: { textDecoration: "none" },
                                        children: (0, l.jsx)(d.M, {
                                          label: e,
                                          variant: "outline",
                                        }),
                                      },
                                      e,
                                    ),
                                  ),
                                }),
                            ],
                          }),
                        ],
                      },
                      e.slug ?? r,
                    ),
                  ),
                }),
              ],
            }),
          ],
        });
      }
      function g({ rules: e, summary: r }) {
        const [s, t] = (0, n.useState)("all"),
          [a, o] = (0, n.useState)(0),
          i = "all" === s ? e : e.filter((e) => e.tags?.includes(s));
        (0, n.useEffect)(() => {
          const e = i.some((e) => !e.passed);
          o(e ? 0 : 1);
        }, [s]);
        const d =
            0 === a ? i.filter((e) => !e.passed) : i.filter((e) => e.passed),
          u = Object.entries(
            d.reduce((e, r) => {
              const s = r.level ?? "Other";
              return ((e[s] ??= []).push(r), e);
            }, {}),
          ).sort(([e], [r]) => m(e) - m(r)),
          p = r?.by_tag ?? {};
        return (0, l.jsxs)("div", {
          children: [
            Object.keys(p).length > 0 &&
              (0, l.jsx)("div", {
                style: {
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  gap: "0.75rem",
                  marginBottom: "1.5rem",
                },
                children: Object.entries(p)
                  .sort(([e], [r]) => e.localeCompare(r))
                  .map(([e, r]) =>
                    (0, l.jsxs)(
                      "button",
                      {
                        type: "button",
                        onClick: () => t(s === e ? "all" : e),
                        style: {
                          cursor: "pointer",
                          padding: "0.75rem",
                          textAlign: "center",
                          background: "var(--ifm-card-background-color)",
                          border:
                            s === e
                              ? "2px solid var(--ifm-color-primary)"
                              : "1px solid var(--ifm-color-emphasis-200)",
                          borderRadius: "8px",
                          transform: s === e ? "scale(1.03)" : "scale(1)",
                          transition: "all 0.2s ease",
                        },
                        children: [
                          (0, l.jsx)("small", {
                            style: {
                              textTransform: "uppercase",
                              fontWeight: 700,
                              letterSpacing: "0.05em",
                              opacity: 0.8,
                            },
                            children: e,
                          }),
                          (0, l.jsx)("br", {}),
                          (0, l.jsxs)("span", {
                            style: { fontSize: "1.5rem", fontWeight: 700 },
                            children: [r.score, "%"],
                          }),
                          (0, l.jsx)("br", {}),
                          (0, l.jsxs)("small", {
                            style: { opacity: 0.6 },
                            children: [
                              r.passed_rules.length,
                              " / ",
                              r.rules.length,
                              " passed",
                            ],
                          }),
                          (0, l.jsx)(c.WN, {
                            values: [
                              r.passed_rules.length,
                              r.rules.length - r.passed_rules.length,
                            ],
                            colors: ["emerald", "rose"],
                            showLabels: !1,
                            className: "mt-2",
                          }),
                        ],
                      },
                      e,
                    ),
                  ),
              }),
            (0, l.jsx)(c.fu, {
              index: a,
              onIndexChange: o,
              className: "mb-6",
              children: (0, l.jsxs)(c.wb, {
                children: [
                  (0, l.jsxs)(c.oz, {
                    children: [
                      "Failed (",
                      i.filter((e) => !e.passed).length,
                      ")",
                    ],
                  }),
                  (0, l.jsxs)(c.oz, {
                    children: [
                      "Passed (",
                      i.filter((e) => e.passed).length,
                      ")",
                    ],
                  }),
                ],
              }),
            }),
            0 === u.length
              ? (0, l.jsx)("p", {
                  style: { opacity: 0.6 },
                  children: "No rules match the selected filter.",
                })
              : u.map(([e, r]) => (0, l.jsx)(f, { level: e, rules: r }, e)),
          ],
        });
      }
      function h() {
        const { report: e, loading: r, error: s } = (0, o.e)();
        if (r)
          return (0, l.jsx)("p", { children: "Loading report data\u2026" });
        if (s)
          return (0, l.jsxs)("div", {
            className: "alert alert--danger",
            children: ["Error: ", s],
          });
        if (!e)
          return (0, l.jsx)("p", { children: "No report data available." });
        const t = e.rules ?? e.playbook?.rules ?? [],
          a = e.rules_summary ?? e.playbook?.rules_summary;
        return 0 === t.length
          ? (0, l.jsx)("div", {
              className: "alert alert--info",
              children: "No rules were evaluated in this report.",
            })
          : (0, l.jsx)(g, { rules: t, summary: a });
      }
      const x = { title: "Rules", hide_title: !0 },
        j = void 0,
        b = {},
        v = [];
      function y(e) {
        return (0, l.jsx)(h, {});
      }
      function k(e = {}) {
        const { wrapper: r } = { ...(0, a.R)(), ...e.components };
        return r
          ? (0, l.jsx)(r, { ...e, children: (0, l.jsx)(y, { ...e }) })
          : y();
      }
    },
    21664(e, r, s) {
      s.d(r, { M: () => a, Z: () => n });
      s(10162);
      var t = s(56730);
      const l = {
        info: {
          background: "var(--ifm-color-info-contrast-background)",
          color: "var(--ifm-color-info-contrast-foreground)",
          border: "1px solid var(--ifm-color-info-dark)",
        },
        warning: {
          background: "var(--ifm-color-warning-contrast-background)",
          color: "var(--ifm-color-warning-contrast-foreground)",
          border: "1px solid var(--ifm-color-warning-dark)",
        },
        critical: {
          background: "var(--ifm-color-danger-contrast-background)",
          color: "var(--ifm-color-danger-contrast-foreground)",
          border: "1px solid var(--ifm-color-danger-dark)",
        },
        success: {
          background: "var(--ifm-color-success-contrast-background)",
          color: "var(--ifm-color-success-contrast-foreground)",
          border: "1px solid var(--ifm-color-success-dark)",
        },
        outline: {
          background: "transparent",
          color: "var(--ifm-font-color-base)",
          border: "1px solid var(--ifm-color-emphasis-300)",
        },
        default: {
          background: "var(--ifm-color-emphasis-200)",
          color: "var(--ifm-font-color-base)",
          border: "1px solid var(--ifm-color-emphasis-300)",
        },
      };
      function a({ label: e, variant: r = "default", size: s = "sm" }) {
        const a = {
          ...(l[r] ?? l.default),
          padding: "lg" === s ? "0.3rem 1rem" : "0.15rem 0.5rem",
          borderRadius: "lg" === s ? "6px" : "4px",
          fontSize: "lg" === s ? "1.5rem" : "0.75rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          display: "inline-block",
          lineHeight: 1.4,
        };
        return (0, t.jsx)("span", { style: a, children: e });
      }
      function n(e) {
        switch (e?.toLowerCase()) {
          case "critical":
            return "critical";
          case "warning":
            return "warning";
          case "info":
            return "info";
          case "gold":
          case "silver":
          case "bronze":
            return "success";
          default:
            return "default";
        }
      }
    },
  },
]);
