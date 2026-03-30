"use strict";
(globalThis.webpackChunk_regis_cli_report_viewer =
  globalThis.webpackChunk_regis_cli_report_viewer || []).push([
  [308],
  {
    15922(e, r, s) {
      (s.r(r),
        s.d(r, {
          assets: () => N,
          contentTitle: () => y,
          default: () => z,
          frontMatter: () => v,
          metadata: () => t,
          toc: () => w,
        }));
      const t = JSON.parse(
        '{"id":"index","title":"index","description":"","source":"@site/docs/index.mdx","sourceDirName":".","slug":"/","permalink":"/","draft":false,"unlisted":false,"tags":[],"version":"current","frontMatter":{"slug":"/","hide_title":true},"sidebar":"defaultSidebar","next":{"title":"Rules","permalink":"/rules"}}',
      );
      var a = s(56730),
        n = s(59336),
        l = (s(10162), s(25821)),
        i = s(17879),
        o = s(81450),
        c = s(21664);
      const d = {
        gold: {
          icon: "",
          gradient: "linear-gradient(135deg, #f9a825, #ff8f00)",
        },
        silver: {
          icon: "",
          gradient: "linear-gradient(135deg, #90a4ae, #607d8b)",
        },
        bronze: {
          icon: "",
          gradient: "linear-gradient(135deg, #a1887f, #795548)",
        },
        none: {
          icon: "",
          gradient: "linear-gradient(135deg, #757575, #424242)",
        },
      };
      function m({ tier: e, size: r = "md" }) {
        const s = d[e?.toLowerCase()] ?? d.none,
          t = "sm" === r;
        return (0, a.jsxs)("span", {
          style: {
            display: "inline-flex",
            alignItems: "center",
            gap: t ? "0.2rem" : "0.4rem",
            background: s.gradient,
            color: "#fff",
            padding: t ? "0.15rem 0.45rem" : "0.3rem 0.8rem",
            borderRadius: t ? "4px" : "6px",
            fontSize: t ? "0.7rem" : "0.9rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          },
          children: [
            (0, a.jsx)("span", {
              style: { fontSize: t ? "0.8rem" : "1.1rem" },
              children: s.icon,
            }),
            e,
          ],
        });
      }
      function x({
        score: e,
        label: r,
        passed: s,
        total: t,
        subtitle: n,
        tier: i,
      }) {
        const o = Math.max(0, (t ?? 0) - (s ?? 0)),
          c = e >= 80 ? "emerald" : e >= 50 ? "amber" : "rose";
        return (0, a.jsxs)(l.Zp, {
          className: "flex flex-col",
          children: [
            (0, a.jsxs)(l.so, {
              justifyContent: "between",
              alignItems: "start",
              children: [
                (0, a.jsx)(l.EY, { className: "font-medium", children: r }),
                i
                  ? (0, a.jsx)(m, { tier: i, size: "sm" })
                  : (0, a.jsxs)(l.Ex, {
                      color: c,
                      size: "xs",
                      children: [e, "%"],
                    }),
              ],
            }),
            (0, a.jsx)("div", {
              className: "flex flex-1 items-center justify-center my-4",
              children: (0, a.jsxs)("span", {
                style: { fontSize: "3.75rem", fontWeight: 700, lineHeight: 1 },
                className:
                  "emerald" === c
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "amber" === c
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-rose-600 dark:text-rose-400",
                children: [e, "%"],
              }),
            }),
            n &&
              (0, a.jsx)(l.EY, {
                className: "text-tremor-default text-tremor-content",
                children: n,
              }),
            void 0 !== t &&
              t > 0 &&
              (0, a.jsx)(a.Fragment, {
                children: (0, a.jsx)(l.WN, {
                  values: [s ?? 0, o],
                  colors: ["emerald", "rose"],
                  className: "mt-4",
                  showLabels: !1,
                }),
              }),
          ],
        });
      }
      function u({ analyzers: e, totalExpected: r = 12 }) {
        const s = Math.round((e.length / r) * 100),
          t = s >= 80 ? "emerald" : s >= 50 ? "amber" : "rose";
        return (0, a.jsxs)(l.Zp, {
          className: "flex flex-col",
          children: [
            (0, a.jsxs)(l.so, {
              justifyContent: "between",
              alignItems: "start",
              children: [
                (0, a.jsx)(l.EY, {
                  className: "font-medium",
                  children: "Analyzer Coverage",
                }),
                (0, a.jsxs)(l.Ex, {
                  color: t,
                  size: "xs",
                  children: [e.length, " run"],
                }),
              ],
            }),
            (0, a.jsx)("div", {
              className: "flex flex-1 items-center justify-center my-4",
              children: (0, a.jsxs)("span", {
                style: { fontSize: "3.75rem", fontWeight: 700, lineHeight: 1 },
                className:
                  "emerald" === t
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "amber" === t
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-rose-600 dark:text-rose-400",
                children: [s, "%"],
              }),
            }),
            (0, a.jsx)(l.z2, { value: s, color: t, className: "mt-4" }),
          ],
        });
      }
      const f = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];
      function g(e) {
        const r = f.findIndex((r) => r.toLowerCase() === e?.toLowerCase());
        return -1 === r ? f.length : r;
      }
      function h({ rules: e }) {
        const r = e.reduce((e, r) => {
            const s = r.level ?? "Other";
            return (
              (e[s] ??= { passed: 0, failed: 0, incomplete: 0 }),
              "incomplete" === r.status
                ? e[s].incomplete++
                : r.passed
                  ? e[s].passed++
                  : e[s].failed++,
              e
            );
          }, {}),
          s = Object.entries(r).sort(([e], [r]) => g(e) - g(r));
        return 0 === s.length
          ? null
          : (0, a.jsxs)(l.Zp, {
              children: [
                (0, a.jsx)(l.EY, {
                  className: "font-medium mb-4",
                  children: "Rules by Level",
                }),
                (0, a.jsx)("div", {
                  className: "space-y-4",
                  children: s.map(([e, r]) => {
                    const s = r.passed + r.failed + r.incomplete;
                    return (0, a.jsxs)(
                      "div",
                      {
                        children: [
                          (0, a.jsxs)(l.so, {
                            justifyContent: "between",
                            alignItems: "center",
                            className: "mb-1",
                            children: [
                              (0, a.jsx)(c.M, {
                                label: e,
                                variant: (0, c.Z)(e),
                              }),
                              (0, a.jsxs)(l.EY, {
                                className:
                                  "text-tremor-label text-tremor-content",
                                children: [r.passed, "/", s, " passed"],
                              }),
                            ],
                          }),
                          (0, a.jsx)(l.WN, {
                            values: [r.passed, r.failed, r.incomplete],
                            colors: ["emerald", "rose", "amber"],
                            showLabels: !1,
                          }),
                        ],
                      },
                      e,
                    );
                  }),
                }),
              ],
            });
      }
      function p({ rules: e }) {
        const r = e.reduce((e, r) => {
            for (const s of r.tags ?? [])
              ((e[s] ??= { passed: 0, failed: 0, incomplete: 0 }),
                "incomplete" === r.status
                  ? e[s].incomplete++
                  : r.passed
                    ? e[s].passed++
                    : e[s].failed++);
            return e;
          }, {}),
          s = Object.entries(r).sort(([e], [r]) => e.localeCompare(r));
        return 0 === s.length
          ? null
          : (0, a.jsxs)(l.Zp, {
              children: [
                (0, a.jsx)(l.EY, {
                  className: "font-medium mb-4",
                  children: "Rules by Tag",
                }),
                (0, a.jsx)("div", {
                  className: "space-y-4",
                  children: s.map(([e, r]) => {
                    const s = r.passed + r.failed + r.incomplete,
                      t = Math.round((r.passed / s) * 100);
                    return (0, a.jsxs)(
                      "div",
                      {
                        children: [
                          (0, a.jsxs)(l.so, {
                            justifyContent: "between",
                            alignItems: "center",
                            className: "mb-1",
                            children: [
                              (0, a.jsx)(l.EY, {
                                className:
                                  "text-tremor-default font-medium capitalize",
                                children: e,
                              }),
                              (0, a.jsxs)(l.EY, {
                                className:
                                  "text-tremor-label text-tremor-content",
                                children: [
                                  r.passed,
                                  "/",
                                  s,
                                  " passed \xb7 ",
                                  t,
                                  "%",
                                ],
                              }),
                            ],
                          }),
                          (0, a.jsx)(l.WN, {
                            values: [r.passed, r.failed, r.incomplete],
                            colors: ["emerald", "rose", "amber"],
                            showLabels: !1,
                          }),
                        ],
                      },
                      e,
                    );
                  }),
                }),
              ],
            });
      }
      const j = ["Gold", "Silver", "Bronze", "Critical", "Warning", "Info"];
      function b() {
        const { report: e, loading: r, error: s } = (0, o.e)();
        if (r)
          return (0, a.jsx)("p", { children: "Loading report data\u2026" });
        if (s)
          return (0, a.jsxs)("div", {
            className: "alert alert--danger",
            children: ["Error: ", s],
          });
        if (!e)
          return (0, a.jsx)("p", { children: "No report data available." });
        const t = e.request ?? {},
          n = e.playbook ?? e.playbooks?.[0],
          d = e.rules_summary ?? n?.rules_summary,
          m = d?.score ?? 0,
          f = d?.passed,
          g = d?.total,
          b = Array.isArray(f) ? f.length : (f ?? 0),
          v = Array.isArray(g) ? g.length : (g ?? 0),
          y = e.tier ?? n?.tier,
          N = t.analyzers ?? [],
          w = e.results?.trivy,
          k = w
            ? [
                { severity: "Critical", count: w.critical_count ?? 0 },
                { severity: "High", count: w.high_count ?? 0 },
                { severity: "Medium", count: w.medium_count ?? 0 },
                { severity: "Low", count: w.low_count ?? 0 },
                { severity: "Unknown", count: w.unknown_count ?? 0 },
              ]
            : [],
          z = (Math.max(0, v - b), e.rules ?? n?.rules ?? []),
          C = (function (e) {
            const r = new Set(
              e.filter((e) => !e.passed).map((e) => e.level?.toLowerCase()),
            );
            return j.find((e) => r.has(e.toLowerCase())) ?? null;
          })(z);
        (C &&
          z.filter(
            (e) => !e.passed && e.level?.toLowerCase() === C.toLowerCase(),
          ).length,
          k.length > 0 && k.some((e) => e.count > 0));
        return (0, a.jsxs)("div", {
          className: "p-6 space-y-8",
          children: [
            (e.badges?.length ?? 0) > 0 &&
              (0, a.jsx)("header", {
                className: "flex flex-wrap gap-2",
                children: e.badges.map((e, r) => {
                  return (0, a.jsx)(
                    l.Ex,
                    {
                      color:
                        ((s = e.class),
                        "success" === s
                          ? "emerald"
                          : "warning" === s
                            ? "amber"
                            : "error" === s
                              ? "rose"
                              : "information" === s
                                ? "indigo"
                                : "gray"),
                      size: "md",
                      children: e.label,
                    },
                    r,
                  );
                  var s;
                }),
              }),
            (0, a.jsx)("section", {
              children: (0, a.jsxs)(l.xA, {
                numItemsSm: 1,
                numItemsLg: 3,
                className: "gap-6",
                children: [
                  (0, a.jsxs)(l.Zp, {
                    className: "flex flex-col",
                    children: [
                      (0, a.jsxs)(l.so, {
                        justifyContent: "between",
                        alignItems: "start",
                        children: [
                          (0, a.jsx)(l.EY, {
                            className: "font-medium",
                            children: "Failure Level",
                          }),
                          z.filter((e) => !e.passed).length > 0 &&
                            (0, a.jsxs)(l.Ex, {
                              color: "rose",
                              size: "xs",
                              children: [
                                z.filter((e) => !e.passed).length,
                                " failed",
                              ],
                            }),
                        ],
                      }),
                      C
                        ? (0, a.jsx)(a.Fragment, {
                            children: (0, a.jsx)("div", {
                              className:
                                "flex flex-1 items-center justify-center",
                              children: (0, a.jsx)(c.M, {
                                label: C,
                                variant: (0, c.Z)(C),
                                size: "lg",
                              }),
                            }),
                          })
                        : (0, a.jsx)("div", {
                            className:
                              "flex flex-1 items-center justify-center",
                            children: (0, a.jsx)(c.M, {
                              label: "All rules passed",
                              variant: "success",
                              size: "lg",
                            }),
                          }),
                    ],
                  }),
                  (0, a.jsx)(x, {
                    score: m,
                    label: "Compliance Score",
                    passed: b,
                    total: v,
                    tier: y ?? void 0,
                  }),
                  (0, a.jsx)(u, { analyzers: N }),
                ],
              }),
            }),
            (0, a.jsx)("section", {
              children: (0, a.jsxs)(l.xA, {
                numItemsSm: 1,
                numItemsLg: 2,
                className: "gap-6",
                children: [
                  (0, a.jsx)(h, { rules: z }),
                  (0, a.jsx)(p, { rules: z }),
                ],
              }),
            }),
            z.filter((e) => !e.passed).length > 0 &&
              (() => {
                const e = z
                    .filter((e) => !e.passed)
                    .reduce((e, r) => {
                      const s = r.level ?? "Other";
                      return ((e[s] ??= []).push(r), e);
                    }, {}),
                  r = Object.entries(e).sort(([e], [r]) => {
                    const s = j.findIndex(
                        (r) => r.toLowerCase() === e.toLowerCase(),
                      ),
                      t = j.findIndex(
                        (e) => e.toLowerCase() === r.toLowerCase(),
                      );
                    return (
                      (-1 === s ? j.length : s) - (-1 === t ? j.length : t)
                    );
                  });
                return (0, a.jsxs)("section", {
                  children: [
                    (0, a.jsx)(l.hE, {
                      className: "mb-4",
                      children: "Failed Rules",
                    }),
                    (0, a.jsx)("div", {
                      className: "space-y-6",
                      children: r.map(([e, r]) =>
                        (0, a.jsxs)(
                          "div",
                          {
                            children: [
                              (0, a.jsxs)("div", {
                                className: "flex items-center gap-3 mb-3",
                                children: [
                                  (0, a.jsx)(c.M, {
                                    label: e,
                                    variant: (0, c.Z)(e),
                                  }),
                                  (0, a.jsxs)(l.EY, {
                                    className:
                                      "text-tremor-label text-tremor-content",
                                    children: [r.length, " failed"],
                                  }),
                                ],
                              }),
                              (0, a.jsxs)(l.XI, {
                                children: [
                                  (0, a.jsx)(l.nd, {
                                    children: (0, a.jsxs)(l.Hj, {
                                      children: [
                                        (0, a.jsx)(l.M_, {
                                          style: { width: "3rem" },
                                          children: "Status",
                                        }),
                                        (0, a.jsx)(l.M_, { children: "Rule" }),
                                      ],
                                    }),
                                  }),
                                  (0, a.jsx)(l.BF, {
                                    children: r.map((e, r) =>
                                      (0, a.jsxs)(
                                        l.Hj,
                                        {
                                          children: [
                                            (0, a.jsx)(l.nA, {
                                              style: { textAlign: "center" },
                                              children: (0, a.jsx)("span", {
                                                style: { fontSize: "1.5rem" },
                                                children:
                                                  "incomplete" === e.status
                                                    ? "\u26a0\ufe0f"
                                                    : "\u274c",
                                              }),
                                            }),
                                            (0, a.jsxs)(l.nA, {
                                              children: [
                                                (0, a.jsx)("strong", {
                                                  children:
                                                    e.description ??
                                                    e.title ??
                                                    e.slug,
                                                }),
                                                e.message &&
                                                  (0, a.jsx)(l.EY, {
                                                    className:
                                                      "mt-1 text-tremor-default text-tremor-content",
                                                    children: e.message,
                                                  }),
                                                e.analyzers &&
                                                  e.analyzers.length > 0 &&
                                                  (0, a.jsx)("div", {
                                                    className:
                                                      "flex flex-wrap gap-1 mt-1",
                                                    children: e.analyzers.map(
                                                      (e) =>
                                                        (0, a.jsx)(
                                                          i.A,
                                                          {
                                                            to: `/analyzers/${e}`,
                                                            style: {
                                                              textDecoration:
                                                                "none",
                                                            },
                                                            children: (0,
                                                            a.jsx)(c.M, {
                                                              label: e,
                                                              variant:
                                                                "outline",
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
                          },
                          e,
                        ),
                      ),
                    }),
                  ],
                });
              })(),
            (e.links?.length ?? 0) > 0 &&
              (0, a.jsxs)("section", {
                className: "pt-6 border-t border-gray-200 dark:border-gray-800",
                children: [
                  (0, a.jsx)(l.hE, {
                    className: "mb-4",
                    children: "Resources",
                  }),
                  (0, a.jsx)("div", {
                    className: "flex flex-wrap gap-3",
                    children: e.links?.map((e, r) =>
                      (0, a.jsx)(
                        "a",
                        {
                          href: e.url,
                          target: "_blank",
                          rel: "noopener noreferrer",
                          className:
                            "px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300",
                          children: e.label,
                        },
                        r,
                      ),
                    ),
                  }),
                ],
              }),
          ],
        });
      }
      const v = { slug: "/", hide_title: !0 },
        y = void 0,
        N = {},
        w = [];
      function k(e) {
        return (0, a.jsx)(b, {});
      }
      function z(e = {}) {
        const { wrapper: r } = { ...(0, n.R)(), ...e.components };
        return r
          ? (0, a.jsx)(r, { ...e, children: (0, a.jsx)(k, { ...e }) })
          : k();
      }
    },
    21664(e, r, s) {
      s.d(r, { M: () => n, Z: () => l });
      s(10162);
      var t = s(56730);
      const a = {
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
      function n({ label: e, variant: r = "default", size: s = "sm" }) {
        const n = {
          ...(a[r] ?? a.default),
          padding: "lg" === s ? "0.3rem 1rem" : "0.15rem 0.5rem",
          borderRadius: "lg" === s ? "6px" : "4px",
          fontSize: "lg" === s ? "1.5rem" : "0.75rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          display: "inline-block",
          lineHeight: 1.4,
        };
        return (0, t.jsx)("span", { style: n, children: e });
      }
      function l(e) {
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
