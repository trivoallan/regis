"use strict";
(globalThis.webpackChunk_regis_dashboard =
  globalThis.webpackChunk_regis_dashboard || []).push([
  [9157],
  {
    99533(e, s, a) {
      (a.r(s),
        a.d(s, {
          assets: () => d,
          contentTitle: () => o,
          default: () => u,
          frontMatter: () => i,
          metadata: () => r,
          toc: () => p,
        }));
      const r = JSON.parse(
        '{"id":"analyzers/freshness","title":"Freshness","description":"","source":"@site/docs/analyzers/freshness.mdx","sourceDirName":"analyzers","slug":"/analyzers/freshness","permalink":"/regis/examples/playbooks/default/alpine/report/analyzers/freshness","draft":false,"unlisted":false,"tags":[],"version":"current","frontMatter":{"title":"Freshness","hide_title":true},"sidebar":"defaultSidebar","previous":{"title":"End of Life","permalink":"/regis/examples/playbooks/default/alpine/report/analyzers/endoflife"},"next":{"title":"Hadolint","permalink":"/regis/examples/playbooks/default/alpine/report/analyzers/hadolint"}}',
      );
      var t = a(56730),
        n = a(26451),
        l = a(39796);
      const i = { title: "Freshness", hide_title: !0 },
        o = void 0,
        d = {},
        p = [];
      function f(e) {
        return (0, t.jsx)(l.e, { name: "freshness" });
      }
      function u(e = {}) {
        const { wrapper: s } = { ...(0, n.R)(), ...e.components };
        return s
          ? (0, t.jsx)(s, { ...e, children: (0, t.jsx)(f, { ...e }) })
          : f();
      }
    },
  },
]);
