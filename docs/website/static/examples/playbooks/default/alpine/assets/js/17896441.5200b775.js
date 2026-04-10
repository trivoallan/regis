"use strict";
(globalThis.webpackChunk_regis_dashboard =
  globalThis.webpackChunk_regis_dashboard || []).push([
  [8401],
  {
    19041(e, n, t) {
      (t.r(n), t.d(n, { default: () => An }));
      var s = t(10162),
        a = t(71167),
        i = t(48433),
        r = t(56730);
      const l = s.createContext(null);
      function o({ children: e, content: n }) {
        const t = (function (e) {
          return (0, s.useMemo)(
            () => ({
              metadata: e.metadata,
              frontMatter: e.frontMatter,
              assets: e.assets,
              contentTitle: e.contentTitle,
              toc: e.toc,
            }),
            [e],
          );
        })(n);
        return (0, r.jsx)(l.Provider, { value: t, children: e });
      }
      function c() {
        const e = (0, s.useContext)(l);
        if (null === e) throw new i.dV("DocProvider");
        return e;
      }
      function d() {
        const { metadata: e, frontMatter: n, assets: t } = c();
        return (0, r.jsx)(a.be, {
          title: e.title,
          description: e.description,
          keywords: n.keywords,
          image: t.image ?? n.image,
        });
      }
      var u = t(70851),
        m = t(17578),
        h = t(26135),
        x = t(55450);
      function f(e) {
        const { permalink: n, title: t, subLabel: s, isNext: a } = e;
        return (0, r.jsxs)(x.A, {
          className: (0, u.A)(
            "pagination-nav__link",
            a ? "pagination-nav__link--next" : "pagination-nav__link--prev",
          ),
          to: n,
          children: [
            s &&
              (0, r.jsx)("div", {
                className: "pagination-nav__sublabel",
                children: s,
              }),
            (0, r.jsx)("div", {
              className: "pagination-nav__label",
              children: t,
            }),
          ],
        });
      }
      function p(e) {
        const { className: n, previous: t, next: s } = e;
        return (0, r.jsxs)("nav", {
          className: (0, u.A)(n, "pagination-nav"),
          "aria-label": (0, h.T)({
            id: "theme.docs.paginator.navAriaLabel",
            message: "Docs pages",
            description: "The ARIA label for the docs pagination",
          }),
          children: [
            t &&
              (0, r.jsx)(f, {
                ...t,
                subLabel: (0, r.jsx)(h.A, {
                  id: "theme.docs.paginator.previous",
                  description: "The label used to navigate to the previous doc",
                  children: "Previous",
                }),
              }),
            s &&
              (0, r.jsx)(f, {
                ...s,
                subLabel: (0, r.jsx)(h.A, {
                  id: "theme.docs.paginator.next",
                  description: "The label used to navigate to the next doc",
                  children: "Next",
                }),
                isNext: !0,
              }),
          ],
        });
      }
      function v() {
        const { metadata: e } = c();
        return (0, r.jsx)(p, {
          className: "docusaurus-mt-lg",
          previous: e.previous,
          next: e.next,
        });
      }
      var b = t(84062),
        g = t(75584),
        j = t(27708),
        A = t(18724),
        N = t(49619);
      const _ = {
        unreleased: function ({ siteTitle: e, versionMetadata: n }) {
          return (0, r.jsx)(h.A, {
            id: "theme.docs.versions.unreleasedVersionLabel",
            description:
              "The label used to tell the user that he's browsing an unreleased doc version",
            values: {
              siteTitle: e,
              versionLabel: (0, r.jsx)("b", { children: n.label }),
            },
            children:
              "This is unreleased documentation for {siteTitle} {versionLabel} version.",
          });
        },
        unmaintained: function ({ siteTitle: e, versionMetadata: n }) {
          return (0, r.jsx)(h.A, {
            id: "theme.docs.versions.unmaintainedVersionLabel",
            description:
              "The label used to tell the user that he's browsing an unmaintained doc version",
            values: {
              siteTitle: e,
              versionLabel: (0, r.jsx)("b", { children: n.label }),
            },
            children:
              "This is documentation for {siteTitle} {versionLabel}, which is no longer actively maintained.",
          });
        },
      };
      function L(e) {
        const n = _[e.versionMetadata.banner];
        return (0, r.jsx)(n, { ...e });
      }
      function y({ versionLabel: e, to: n, onClick: t }) {
        return (0, r.jsx)(h.A, {
          id: "theme.docs.versions.latestVersionSuggestionLabel",
          description:
            "The label used to tell the user to check the latest version",
          values: {
            versionLabel: e,
            latestVersionLink: (0, r.jsx)("b", {
              children: (0, r.jsx)(x.A, {
                to: n,
                onClick: t,
                children: (0, r.jsx)(h.A, {
                  id: "theme.docs.versions.latestVersionLinkLabel",
                  description:
                    "The label used for the latest version suggestion link label",
                  children: "latest version",
                }),
              }),
            }),
          },
          children:
            "For up-to-date documentation, see the {latestVersionLink} ({versionLabel}).",
        });
      }
      function T({ className: e, versionMetadata: n }) {
        const {
            siteConfig: { title: t },
          } = (0, b.A)(),
          { pluginId: s } = (0, g.vT)({ failfast: !0 }),
          { savePreferredVersionName: a } = (0, A.g1)(s),
          { latestDocSuggestion: i, latestVersionSuggestion: l } = (0, g.HW)(s),
          o = i ?? (c = l).docs.find((e) => e.id === c.mainDocId);
        var c;
        return (0, r.jsxs)("div", {
          className: (0, u.A)(
            e,
            j.G.docs.docVersionBanner,
            "alert alert--warning margin-bottom--md",
          ),
          role: "alert",
          children: [
            (0, r.jsx)("div", {
              children: (0, r.jsx)(L, { siteTitle: t, versionMetadata: n }),
            }),
            (0, r.jsx)("div", {
              className: "margin-top--md",
              children: (0, r.jsx)(y, {
                versionLabel: l.label,
                to: o.path,
                onClick: () => a(l.name),
              }),
            }),
          ],
        });
      }
      function C({ className: e }) {
        const n = (0, N.r)();
        return n.banner
          ? (0, r.jsx)(T, { className: e, versionMetadata: n })
          : null;
      }
      function k({ className: e }) {
        const n = (0, N.r)();
        return n.badge
          ? (0, r.jsx)("span", {
              className: (0, u.A)(
                e,
                j.G.docs.docVersionBadge,
                "badge badge--secondary",
              ),
              children: (0, r.jsx)(h.A, {
                id: "theme.docs.versionBadge.label",
                values: { versionLabel: n.label },
                children: "Version: {versionLabel}",
              }),
            })
          : null;
      }
      const w = "tag_kZeh",
        H = "tagRegular_aR8Z",
        M = "tagWithCount_K0bi";
      function U({ permalink: e, label: n, count: t, description: s }) {
        return (0, r.jsxs)(x.A, {
          rel: "tag",
          href: e,
          title: s,
          className: (0, u.A)(w, t ? M : H),
          children: [n, t && (0, r.jsx)("span", { children: t })],
        });
      }
      const B = "tags_btIT",
        E = "tag_ssUY";
      function D({ tags: e }) {
        return (0, r.jsxs)(r.Fragment, {
          children: [
            (0, r.jsx)("b", {
              children: (0, r.jsx)(h.A, {
                id: "theme.tags.tagsListLabel",
                description: "The label alongside a tag list",
                children: "Tags:",
              }),
            }),
            (0, r.jsx)("ul", {
              className: (0, u.A)(B, "padding--none", "margin-left--sm"),
              children: e.map((e) =>
                (0, r.jsx)(
                  "li",
                  { className: E, children: (0, r.jsx)(U, { ...e }) },
                  e.permalink,
                ),
              ),
            }),
          ],
        });
      }
      const S = "iconEdit_eZPw";
      function I({ className: e, ...n }) {
        return (0, r.jsx)("svg", {
          fill: "currentColor",
          height: "20",
          width: "20",
          viewBox: "0 0 40 40",
          className: (0, u.A)(S, e),
          "aria-hidden": "true",
          ...n,
          children: (0, r.jsx)("g", {
            children: (0, r.jsx)("path", {
              d: "m34.5 11.7l-3 3.1-6.3-6.3 3.1-3q0.5-0.5 1.2-0.5t1.1 0.5l3.9 3.9q0.5 0.4 0.5 1.1t-0.5 1.2z m-29.5 17.1l18.4-18.5 6.3 6.3-18.4 18.4h-6.3v-6.2z",
            }),
          }),
        });
      }
      function V({ editUrl: e }) {
        return (0, r.jsxs)(x.A, {
          to: e,
          className: j.G.common.editThisPage,
          children: [
            (0, r.jsx)(I, {}),
            (0, r.jsx)(h.A, {
              id: "theme.common.editThisPage",
              description: "The link label to edit the current page",
              children: "Edit this page",
            }),
          ],
        });
      }
      function O(e = {}) {
        const {
            i18n: { currentLocale: n },
          } = (0, b.A)(),
          t = (function () {
            const {
              i18n: { currentLocale: e, localeConfigs: n },
            } = (0, b.A)();
            return n[e].calendar;
          })();
        return new Intl.DateTimeFormat(n, { calendar: t, ...e });
      }
      function R({ lastUpdatedAt: e }) {
        const n = new Date(e),
          t = O({
            day: "numeric",
            month: "short",
            year: "numeric",
            timeZone: "UTC",
          }).format(n);
        return (0, r.jsx)(h.A, {
          id: "theme.lastUpdated.atDate",
          description:
            "The words used to describe on which date a page has been last updated",
          values: {
            date: (0, r.jsx)("b", {
              children: (0, r.jsx)("time", {
                dateTime: n.toISOString(),
                itemProp: "dateModified",
                children: t,
              }),
            }),
          },
          children: " on {date}",
        });
      }
      function G({ lastUpdatedBy: e }) {
        return (0, r.jsx)(h.A, {
          id: "theme.lastUpdated.byUser",
          description:
            "The words used to describe by who the page has been last updated",
          values: { user: (0, r.jsx)("b", { children: e }) },
          children: " by {user}",
        });
      }
      function F({ lastUpdatedAt: e, lastUpdatedBy: n }) {
        return (0, r.jsxs)("span", {
          className: j.G.common.lastUpdated,
          children: [
            (0, r.jsx)(h.A, {
              id: "theme.lastUpdated.lastUpdatedAtBy",
              description:
                "The sentence used to display when a page has been last updated, and by who",
              values: {
                atDate: e ? (0, r.jsx)(R, { lastUpdatedAt: e }) : "",
                byUser: n ? (0, r.jsx)(G, { lastUpdatedBy: n }) : "",
              },
              children: "Last updated{atDate}{byUser}",
            }),
            !1,
          ],
        });
      }
      const P = "lastUpdated_QLTP",
        z = "noPrint_oywp";
      function $({
        className: e,
        editUrl: n,
        lastUpdatedAt: t,
        lastUpdatedBy: s,
      }) {
        return (0, r.jsxs)("div", {
          className: (0, u.A)("row", e),
          children: [
            (0, r.jsx)("div", {
              className: (0, u.A)("col", z),
              children: n && (0, r.jsx)(V, { editUrl: n }),
            }),
            (0, r.jsx)("div", {
              className: (0, u.A)("col", P),
              children:
                (t || s) &&
                (0, r.jsx)(F, { lastUpdatedAt: t, lastUpdatedBy: s }),
            }),
          ],
        });
      }
      function q() {
        const { metadata: e } = c(),
          { editUrl: n, lastUpdatedAt: t, lastUpdatedBy: s, tags: a } = e,
          i = a.length > 0,
          l = !!(n || t || s);
        return i || l
          ? (0, r.jsxs)("footer", {
              className: (0, u.A)(j.G.docs.docFooter, "docusaurus-mt-lg"),
              children: [
                i &&
                  (0, r.jsx)("div", {
                    className: (0, u.A)(
                      "row margin-top--sm",
                      j.G.docs.docFooterTagsRow,
                    ),
                    children: (0, r.jsx)("div", {
                      className: "col",
                      children: (0, r.jsx)(D, { tags: a }),
                    }),
                  }),
                l &&
                  (0, r.jsx)($, {
                    className: (0, u.A)(
                      "margin-top--sm",
                      j.G.docs.docFooterEditMetaRow,
                    ),
                    editUrl: n,
                    lastUpdatedAt: t,
                    lastUpdatedBy: s,
                  }),
              ],
            })
          : null;
      }
      var Z = t(81775),
        J = t(2155);
      function K(e) {
        const n = e.map((e) => ({ ...e, parentIndex: -1, children: [] })),
          t = Array(7).fill(-1);
        n.forEach((e, n) => {
          const s = t.slice(2, e.level);
          ((e.parentIndex = Math.max(...s)), (t[e.level] = n));
        });
        const s = [];
        return (
          n.forEach((e) => {
            const { parentIndex: t, ...a } = e;
            t >= 0 ? n[t].children.push(a) : s.push(a);
          }),
          s
        );
      }
      function W({ toc: e, minHeadingLevel: n, maxHeadingLevel: t }) {
        return e.flatMap((e) => {
          const s = W({
            toc: e.children,
            minHeadingLevel: n,
            maxHeadingLevel: t,
          });
          return (function (e) {
            return e.level >= n && e.level <= t;
          })(e)
            ? [{ ...e, children: s }]
            : s;
        });
      }
      function X(e) {
        const n = e.getBoundingClientRect();
        return n.top === n.bottom ? X(e.parentNode) : n;
      }
      function Y(e, { anchorTopOffset: n }) {
        const t = e.find((e) => X(e).top >= n);
        if (t) {
          return (function (e) {
            return e.top > 0 && e.bottom < window.innerHeight / 2;
          })(X(t))
            ? t
            : (e[e.indexOf(t) - 1] ?? null);
        }
        return e[e.length - 1] ?? null;
      }
      function Q() {
        const e = (0, s.useRef)(0),
          {
            navbar: { hideOnScroll: n },
          } = (0, J.p)();
        return (
          (0, s.useEffect)(() => {
            e.current = n ? 0 : document.querySelector(".navbar").clientHeight;
          }, [n]),
          e
        );
      }
      function ee(e) {
        const n = (0, s.useRef)(void 0),
          t = Q();
        (0, s.useEffect)(() => {
          if (!e) return () => {};
          const {
            linkClassName: s,
            linkActiveClassName: a,
            minHeadingLevel: i,
            maxHeadingLevel: r,
          } = e;
          function l() {
            const e = (function (e) {
                return Array.from(document.getElementsByClassName(e));
              })(s),
              l = (function ({ minHeadingLevel: e, maxHeadingLevel: n }) {
                const t = [];
                for (let s = e; s <= n; s += 1) t.push(`h${s}.anchor`);
                return Array.from(document.querySelectorAll(t.join()));
              })({ minHeadingLevel: i, maxHeadingLevel: r }),
              o = Y(l, { anchorTopOffset: t.current }),
              c = e.find(
                (e) =>
                  o &&
                  o.id ===
                    (function (e) {
                      return decodeURIComponent(
                        e.href.substring(e.href.indexOf("#") + 1),
                      );
                    })(e),
              );
            e.forEach((e) => {
              !(function (e, t) {
                t
                  ? (n.current &&
                      n.current !== e &&
                      n.current.classList.remove(a),
                    e.classList.add(a),
                    (n.current = e))
                  : e.classList.remove(a);
              })(e, e === c);
            });
          }
          return (
            document.addEventListener("scroll", l),
            document.addEventListener("resize", l),
            l(),
            () => {
              (document.removeEventListener("scroll", l),
                document.removeEventListener("resize", l));
            }
          );
        }, [e, t]);
      }
      function ne({ toc: e, className: n, linkClassName: t, isChild: s }) {
        return e.length
          ? (0, r.jsx)("ul", {
              className: s ? void 0 : n,
              children: e.map((e) =>
                (0, r.jsxs)(
                  "li",
                  {
                    children: [
                      (0, r.jsx)(x.A, {
                        to: `#${e.id}`,
                        className: t ?? void 0,
                        dangerouslySetInnerHTML: { __html: e.value },
                      }),
                      (0, r.jsx)(ne, {
                        isChild: !0,
                        toc: e.children,
                        className: n,
                        linkClassName: t,
                      }),
                    ],
                  },
                  e.id,
                ),
              ),
            })
          : null;
      }
      const te = s.memo(ne);
      function se({
        toc: e,
        className: n = "table-of-contents table-of-contents__left-border",
        linkClassName: t = "table-of-contents__link",
        linkActiveClassName: a,
        minHeadingLevel: i,
        maxHeadingLevel: l,
        ...o
      }) {
        const c = (0, J.p)(),
          d = i ?? c.tableOfContents.minHeadingLevel,
          u = l ?? c.tableOfContents.maxHeadingLevel,
          m = (function ({ toc: e, minHeadingLevel: n, maxHeadingLevel: t }) {
            return (0, s.useMemo)(
              () => W({ toc: K(e), minHeadingLevel: n, maxHeadingLevel: t }),
              [e, n, t],
            );
          })({ toc: e, minHeadingLevel: d, maxHeadingLevel: u });
        return (
          ee(
            (0, s.useMemo)(() => {
              if (t && a)
                return {
                  linkClassName: t,
                  linkActiveClassName: a,
                  minHeadingLevel: d,
                  maxHeadingLevel: u,
                };
            }, [t, a, d, u]),
          ),
          (0, r.jsx)(te, { toc: m, className: n, linkClassName: t, ...o })
        );
      }
      const ae = "tocCollapsibleButton_CShG",
        ie = "tocCollapsibleButtonExpanded_m6ws";
      function re({ collapsed: e, ...n }) {
        return (0, r.jsx)("button", {
          type: "button",
          ...n,
          className: (0, u.A)("clean-btn", ae, !e && ie, n.className),
          children: (0, r.jsx)(h.A, {
            id: "theme.TOCCollapsible.toggleButtonLabel",
            description:
              "The label used by the button on the collapsible TOC component",
            children: "On this page",
          }),
        });
      }
      const le = "tocCollapsible_tbTb",
        oe = "tocCollapsibleContent_X9yl",
        ce = "tocCollapsibleExpanded_wbea";
      function de({
        toc: e,
        className: n,
        minHeadingLevel: t,
        maxHeadingLevel: s,
      }) {
        const { collapsed: a, toggleCollapsed: i } = (0, Z.u)({
          initialState: !0,
        });
        return (0, r.jsxs)("div", {
          className: (0, u.A)(le, !a && ce, n),
          children: [
            (0, r.jsx)(re, { collapsed: a, onClick: i }),
            (0, r.jsx)(Z.N, {
              lazy: !0,
              className: oe,
              collapsed: a,
              children: (0, r.jsx)(se, {
                toc: e,
                minHeadingLevel: t,
                maxHeadingLevel: s,
              }),
            }),
          ],
        });
      }
      const ue = "tocMobile_n_Gf";
      function me() {
        const { toc: e, frontMatter: n } = c();
        return (0, r.jsx)(de, {
          toc: e,
          minHeadingLevel: n.toc_min_heading_level,
          maxHeadingLevel: n.toc_max_heading_level,
          className: (0, u.A)(j.G.docs.docTocMobile, ue),
        });
      }
      const he = "tableOfContents_C27A";
      function xe({ className: e, ...n }) {
        return (0, r.jsx)("div", {
          className: (0, u.A)(he, "thin-scrollbar", e),
          children: (0, r.jsx)(se, {
            ...n,
            linkClassName: "table-of-contents__link toc-highlight",
            linkActiveClassName: "table-of-contents__link--active",
          }),
        });
      }
      function fe() {
        const { toc: e, frontMatter: n } = c();
        return (0, r.jsx)(xe, {
          toc: e,
          minHeadingLevel: n.toc_min_heading_level,
          maxHeadingLevel: n.toc_max_heading_level,
          className: j.G.docs.docTocDesktop,
        });
      }
      var pe = t(73885),
        ve = t(26451),
        be = t(52608),
        ge = t(72976);
      function je(e) {
        return (0, r.jsx)("code", { ...e });
      }
      var Ae = t(49081);
      var Ne = t(22549),
        _e = t(59227);
      const Le = "details_T2lc",
        ye = "isBrowser_M0Cp",
        Te = "collapsibleContent_OiVl";
      function Ce(e) {
        return !!e && ("SUMMARY" === e.tagName || Ce(e.parentElement));
      }
      function ke(e, n) {
        return !!e && (e === n || ke(e.parentElement, n));
      }
      function we({ summary: e, children: n, ...t }) {
        (0, Ne.A)().collectAnchor(t.id);
        const a = (0, _e.A)(),
          i = (0, s.useRef)(null),
          { collapsed: l, setCollapsed: o } = (0, Z.u)({
            initialState: !t.open,
          }),
          [c, d] = (0, s.useState)(t.open),
          m = s.isValidElement(e)
            ? e
            : (0, r.jsx)("summary", { children: e ?? "Details" });
        return (0, r.jsxs)("details", {
          ...t,
          ref: i,
          open: c,
          "data-collapsed": l,
          className: (0, u.A)(Le, a && ye, t.className),
          onMouseDown: (e) => {
            Ce(e.target) && e.detail > 1 && e.preventDefault();
          },
          onClick: (e) => {
            e.stopPropagation();
            const n = e.target;
            Ce(n) &&
              ke(n, i.current) &&
              (e.preventDefault(), l ? (o(!1), d(!0)) : o(!0));
          },
          children: [
            m,
            (0, r.jsx)(Z.N, {
              lazy: !1,
              collapsed: l,
              onCollapseTransitionEnd: (e) => {
                (o(e), d(!e));
              },
              children: (0, r.jsx)("div", { className: Te, children: n }),
            }),
          ],
        });
      }
      const He = "details_pU2R";
      function Me({ ...e }) {
        return (0, r.jsx)(we, {
          ...e,
          className: (0, u.A)("alert alert--info", He, e.className),
        });
      }
      function Ue(e) {
        const n = s.Children.toArray(e.children),
          t = n.find((e) => s.isValidElement(e) && "summary" === e.type),
          a = (0, r.jsx)(r.Fragment, { children: n.filter((e) => e !== t) });
        return (0, r.jsx)(Me, { ...e, summary: t, children: a });
      }
      function Be(e) {
        return (0, r.jsx)(pe.A, { ...e });
      }
      const Ee = "containsTaskList_JnPB";
      function De(e) {
        if (void 0 !== e)
          return (0, u.A)(e, e?.includes("contains-task-list") && Ee);
      }
      const Se = "img_MOD7";
      var Ie = t(21505),
        Ve = t(88426),
        Oe = t(62111),
        Re = t(38340);
      let Ge = null;
      async function Fe() {
        return (
          Ge ||
            (Ge = (async function () {
              return (
                await Promise.all([t.e(2076), t.e(1466)]).then(t.bind(t, 91466))
              ).default;
            })()),
          Ge
        );
      }
      function Pe() {
        const { colorMode: e } = (0, Re.G)(),
          n = (0, J.p)().mermaid,
          t = n.theme[e],
          { options: a } = n;
        return (0, s.useMemo)(
          () => ({ startOnLoad: !1, ...a, theme: t }),
          [t, a],
        );
      }
      function ze({ text: e, config: n }) {
        const [t, a] = (0, s.useState)(null),
          i = (0, s.useState)(
            `mermaid-svg-${Math.round(1e7 * Math.random())}`,
          )[0],
          r = Pe(),
          l = n ?? r;
        return (
          (0, s.useEffect)(() => {
            (async function ({ id: e, text: n, config: t }) {
              const s = await Fe();
              s.initialize(t);
              try {
                return await s.render(e, n);
              } catch (a) {
                throw (document.querySelector(`#d${e}`)?.remove(), a);
              }
            })({ id: i, text: e, config: l })
              .then(a)
              .catch((e) => {
                a(() => {
                  throw e;
                });
              });
          }, [i, e, l]),
          t
        );
      }
      const $e = "container_MKX7";
      function qe({ renderResult: e }) {
        const n = (0, s.useRef)(null);
        return (
          (0, s.useEffect)(() => {
            const t = n.current;
            e.bindFunctions?.(t);
          }, [e]),
          (0, r.jsx)("div", {
            ref: n,
            className: `docusaurus-mermaid-container ${$e}`,
            dangerouslySetInnerHTML: { __html: e.svg },
          })
        );
      }
      function Ze({ value: e }) {
        const n = ze({ text: e });
        return null === n ? null : (0, r.jsx)(qe, { renderResult: n });
      }
      const Je = {
        Head: be.A,
        details: Ue,
        Details: Ue,
        code: function (e) {
          return (function (e) {
            return (
              void 0 !== e.children &&
              s.Children.toArray(e.children).every(
                (e) => "string" == typeof e && !e.includes("\n"),
              )
            );
          })(e)
            ? (0, r.jsx)(je, { ...e })
            : (0, r.jsx)(ge.A, { ...e });
        },
        a: function (e) {
          const n = (0, Ae.v)(e.id);
          return (0, r.jsx)(x.A, { ...e, className: (0, u.A)(n, e.className) });
        },
        pre: function (e) {
          return (0, r.jsx)(r.Fragment, { children: e.children });
        },
        ul: function (e) {
          return (0, r.jsx)("ul", { ...e, className: De(e.className) });
        },
        li: function (e) {
          (0, Ne.A)().collectAnchor(e.id);
          const n = (0, Ae.v)(e.id);
          return (0, r.jsx)("li", {
            className: (0, u.A)(n, e.className),
            ...e,
          });
        },
        img: function (e) {
          return (0, r.jsx)("img", {
            decoding: "async",
            loading: "lazy",
            ...e,
            className: ((n = e.className), (0, u.A)(n, Se)),
          });
          var n;
        },
        h1: (e) => (0, r.jsx)(Be, { as: "h1", ...e }),
        h2: (e) => (0, r.jsx)(Be, { as: "h2", ...e }),
        h3: (e) => (0, r.jsx)(Be, { as: "h3", ...e }),
        h4: (e) => (0, r.jsx)(Be, { as: "h4", ...e }),
        h5: (e) => (0, r.jsx)(Be, { as: "h5", ...e }),
        h6: (e) => (0, r.jsx)(Be, { as: "h6", ...e }),
        admonition: Ie.A,
        mermaid: function (e) {
          return (0, r.jsx)(Ve.A, {
            fallback: (e) => (0, r.jsx)(Oe.MN, { ...e }),
            children: (0, r.jsx)(Ze, { ...e }),
          });
        },
      };
      function Ke({ children: e }) {
        return (0, r.jsx)(ve.x, { components: Je, children: e });
      }
      function We({ children: e }) {
        const n = (function () {
          const { metadata: e, frontMatter: n, contentTitle: t } = c();
          return n.hide_title || void 0 !== t ? null : e.title;
        })();
        return (0, r.jsxs)("div", {
          className: (0, u.A)(j.G.docs.docMarkdown, "markdown"),
          children: [
            n &&
              (0, r.jsx)("header", {
                children: (0, r.jsx)(pe.A, { as: "h1", children: n }),
              }),
            (0, r.jsx)(Ke, { children: e }),
          ],
        });
      }
      var Xe = t(12413),
        Ye = t(77334),
        Qe = t(3781);
      function en(e) {
        return (0, r.jsx)("svg", {
          viewBox: "0 0 24 24",
          ...e,
          children: (0, r.jsx)("path", {
            d: "M10 19v-5h4v5c0 .55.45 1 1 1h3c.55 0 1-.45 1-1v-7h1.7c.46 0 .68-.57.33-.87L12.67 3.6c-.38-.34-.96-.34-1.34 0l-8.36 7.53c-.34.3-.13.87.33.87H5v7c0 .55.45 1 1 1h3c.55 0 1-.45 1-1z",
            fill: "currentColor",
          }),
        });
      }
      const nn = "breadcrumbHomeIcon_NfMw";
      function tn() {
        const e = (0, Qe.Ay)("/");
        return (0, r.jsx)("li", {
          className: "breadcrumbs__item",
          children: (0, r.jsx)(x.A, {
            "aria-label": (0, h.T)({
              id: "theme.docs.breadcrumbs.home",
              message: "Home page",
              description:
                "The ARIA label for the home page in the breadcrumbs",
            }),
            className: "breadcrumbs__link",
            href: e,
            children: (0, r.jsx)(en, { className: nn }),
          }),
        });
      }
      function sn(e) {
        const n = (function ({ breadcrumbs: e }) {
          const { siteConfig: n } = (0, b.A)();
          return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            itemListElement: e
              .filter((e) => e.href)
              .map((e, t) => ({
                "@type": "ListItem",
                position: t + 1,
                name: e.label,
                item: `${n.url}${e.href}`,
              })),
          };
        })({ breadcrumbs: e.breadcrumbs });
        return (0, r.jsx)(be.A, {
          children: (0, r.jsx)("script", {
            type: "application/ld+json",
            children: JSON.stringify(n),
          }),
        });
      }
      const an = "breadcrumbsContainer_E_Dm";
      function rn({ children: e, href: n, isLast: t }) {
        const s = "breadcrumbs__link";
        return t
          ? (0, r.jsx)("span", { className: s, children: e })
          : n
            ? (0, r.jsx)(x.A, {
                className: s,
                href: n,
                children: (0, r.jsx)("span", { children: e }),
              })
            : (0, r.jsx)("span", { className: s, children: e });
      }
      function ln({ children: e, active: n }) {
        return (0, r.jsx)("li", {
          className: (0, u.A)("breadcrumbs__item", {
            "breadcrumbs__item--active": n,
          }),
          children: e,
        });
      }
      function on() {
        const e = (0, Xe.OF)(),
          n = (0, Ye.Dt)();
        return e
          ? (0, r.jsxs)(r.Fragment, {
              children: [
                (0, r.jsx)(sn, { breadcrumbs: e }),
                (0, r.jsx)("nav", {
                  className: (0, u.A)(j.G.docs.docBreadcrumbs, an),
                  "aria-label": (0, h.T)({
                    id: "theme.docs.breadcrumbs.navAriaLabel",
                    message: "Breadcrumbs",
                    description: "The ARIA label for the breadcrumbs",
                  }),
                  children: (0, r.jsxs)("ul", {
                    className: "breadcrumbs",
                    children: [
                      n && (0, r.jsx)(tn, {}),
                      e.map((n, t) => {
                        const s = t === e.length - 1,
                          a =
                            "category" === n.type && n.linkUnlisted
                              ? void 0
                              : n.href;
                        return (0, r.jsx)(
                          ln,
                          {
                            active: s,
                            children: (0, r.jsx)(rn, {
                              href: a,
                              isLast: s,
                              children: n.label,
                            }),
                          },
                          t,
                        );
                      }),
                    ],
                  }),
                }),
              ],
            })
          : null;
      }
      function cn() {
        return (0, r.jsx)(h.A, {
          id: "theme.contentVisibility.unlistedBanner.title",
          description: "The unlisted content banner title",
          children: "Unlisted page",
        });
      }
      function dn() {
        return (0, r.jsx)(h.A, {
          id: "theme.contentVisibility.unlistedBanner.message",
          description: "The unlisted content banner message",
          children:
            "This page is unlisted. Search engines will not index it, and only users having a direct link can access it.",
        });
      }
      function un() {
        return (0, r.jsx)(be.A, {
          children: (0, r.jsx)("meta", {
            name: "robots",
            content: "noindex, nofollow",
          }),
        });
      }
      function mn() {
        return (0, r.jsx)(h.A, {
          id: "theme.contentVisibility.draftBanner.title",
          description: "The draft content banner title",
          children: "Draft page",
        });
      }
      function hn() {
        return (0, r.jsx)(h.A, {
          id: "theme.contentVisibility.draftBanner.message",
          description: "The draft content banner message",
          children:
            "This page is a draft. It will only be visible in dev and be excluded from the production build.",
        });
      }
      function xn({ className: e }) {
        return (0, r.jsx)(Ie.A, {
          type: "caution",
          title: (0, r.jsx)(mn, {}),
          className: (0, u.A)(e, j.G.common.draftBanner),
          children: (0, r.jsx)(hn, {}),
        });
      }
      function fn({ className: e }) {
        return (0, r.jsx)(Ie.A, {
          type: "caution",
          title: (0, r.jsx)(cn, {}),
          className: (0, u.A)(e, j.G.common.unlistedBanner),
          children: (0, r.jsx)(dn, {}),
        });
      }
      function pn(e) {
        return (0, r.jsxs)(r.Fragment, {
          children: [(0, r.jsx)(un, {}), (0, r.jsx)(fn, { ...e })],
        });
      }
      function vn({ metadata: e }) {
        const { unlisted: n, frontMatter: t } = e;
        return (0, r.jsxs)(r.Fragment, {
          children: [
            (n || t.unlisted) && (0, r.jsx)(pn, {}),
            t.draft && (0, r.jsx)(xn, {}),
          ],
        });
      }
      const bn = "docItemContainer_bEf2",
        gn = "docItemCol_DbHr";
      function jn({ children: e }) {
        const n = (function () {
            const { frontMatter: e, toc: n } = c(),
              t = (0, m.l)(),
              s = e.hide_table_of_contents,
              a = !s && n.length > 0;
            return {
              hidden: s,
              mobile: a ? (0, r.jsx)(me, {}) : void 0,
              desktop:
                !a || ("desktop" !== t && "ssr" !== t)
                  ? void 0
                  : (0, r.jsx)(fe, {}),
            };
          })(),
          { metadata: t } = c();
        return (0, r.jsxs)("div", {
          className: "row",
          children: [
            (0, r.jsxs)("div", {
              className: (0, u.A)("col", !n.hidden && gn),
              children: [
                (0, r.jsx)(vn, { metadata: t }),
                (0, r.jsx)(C, {}),
                (0, r.jsxs)("div", {
                  className: bn,
                  children: [
                    (0, r.jsxs)("article", {
                      children: [
                        (0, r.jsx)(on, {}),
                        (0, r.jsx)(k, {}),
                        n.mobile,
                        (0, r.jsx)(We, { children: e }),
                        (0, r.jsx)(q, {}),
                      ],
                    }),
                    (0, r.jsx)(v, {}),
                  ],
                }),
              ],
            }),
            n.desktop &&
              (0, r.jsx)("div", {
                className: "col col--3",
                children: n.desktop,
              }),
          ],
        });
      }
      function An(e) {
        const n = `docs-doc-id-${e.content.metadata.id}`,
          t = e.content;
        return (0, r.jsx)(o, {
          content: e.content,
          children: (0, r.jsxs)(a.e3, {
            className: n,
            children: [
              (0, r.jsx)(d, {}),
              (0, r.jsx)(jn, { children: (0, r.jsx)(t, {}) }),
            ],
          }),
        });
      }
    },
  },
]);
