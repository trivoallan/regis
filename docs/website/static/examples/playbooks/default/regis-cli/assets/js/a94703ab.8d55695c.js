"use strict";
(globalThis.webpackChunk_regis_cli_report_viewer =
  globalThis.webpackChunk_regis_cli_report_viewer || []).push([
  [9048],
  {
    9369(e, t, a) {
      (a.r(t), a.d(t, { default: () => Te }));
      var n = a(10162),
        i = a(70851),
        s = a(65288),
        o = a(5043),
        l = a(49109),
        r = a(68539),
        c = a(92010),
        d = a(37964),
        u = a(38418);
      const m = "backToTopButton_CmOW",
        h = "backToTopButtonShow_yIrK";
      var b = a(56730);
      function p() {
        const { shown: e, scrollToTop: t } = (function ({ threshold: e }) {
          const [t, a] = (0, n.useState)(!1),
            i = (0, n.useRef)(!1),
            { startScroll: s, cancelScroll: o } = (0, d.gk)();
          return (
            (0, d.Mq)(({ scrollY: t }, n) => {
              const s = n?.scrollY;
              s &&
                (i.current
                  ? (i.current = !1)
                  : t >= s
                    ? (o(), a(!1))
                    : t < e
                      ? a(!1)
                      : t + window.innerHeight <
                          document.documentElement.scrollHeight && a(!0));
            }),
            (0, u.$)((e) => {
              e.location.hash && ((i.current = !0), a(!1));
            }),
            { shown: t, scrollToTop: () => s(0) }
          );
        })({ threshold: 300 });
        return (0, b.jsx)("button", {
          "aria-label": (0, c.T)({
            id: "theme.BackToTopButton.buttonAriaLabel",
            message: "Scroll back to top",
            description: "The ARIA label for the back to top button",
          }),
          className: (0, i.A)(
            "clean-btn",
            o.G.common.backToTopButton,
            m,
            e && h,
          ),
          type: "button",
          onClick: t,
        });
      }
      var x = a(21497),
        j = a(79139),
        g = a(22601),
        f = a(57306),
        _ = a(17879),
        v = a(21580),
        C = a(3871),
        A = a(62334);
      function k({ logo: e, alt: t, imageClassName: a }) {
        const n = {
            light: (0, v.Ay)(e.src),
            dark: (0, v.Ay)(e.srcDark || e.src),
          },
          i = (0, b.jsx)(A.A, {
            className: e.className,
            sources: n,
            height: e.height,
            width: e.width,
            alt: t,
            style: e.style,
          });
        return a ? (0, b.jsx)("div", { className: a, children: i }) : i;
      }
      function N(e) {
        const {
            siteConfig: { title: t },
          } = (0, C.A)(),
          {
            navbar: { title: a, logo: n },
          } = (0, f.p)(),
          { imageClassName: i, titleClassName: s, ...o } = e,
          l = (0, v.Ay)(n?.href || "/"),
          r = a ? "" : t,
          c = n?.alt ?? r;
        return (0, b.jsxs)(_.A, {
          to: l,
          ...o,
          ...(n?.target && { target: n.target }),
          children: [
            n && (0, b.jsx)(k, { logo: n, alt: c, imageClassName: i }),
            null != a && (0, b.jsx)("b", { className: s, children: a }),
          ],
        });
      }
      function S(e) {
        return (0, b.jsx)("svg", {
          width: "20",
          height: "20",
          "aria-hidden": "true",
          ...e,
          children: (0, b.jsxs)("g", {
            fill: "#7a7a7a",
            children: [
              (0, b.jsx)("path", {
                d: "M9.992 10.023c0 .2-.062.399-.172.547l-4.996 7.492a.982.982 0 01-.828.454H1c-.55 0-1-.453-1-1 0-.2.059-.403.168-.551l4.629-6.942L.168 3.078A.939.939 0 010 2.528c0-.548.45-.997 1-.997h2.996c.352 0 .649.18.828.45L9.82 9.472c.11.148.172.347.172.55zm0 0",
              }),
              (0, b.jsx)("path", {
                d: "M19.98 10.023c0 .2-.058.399-.168.547l-4.996 7.492a.987.987 0 01-.828.454h-3c-.547 0-.996-.453-.996-1 0-.2.059-.403.168-.551l4.625-6.942-4.625-6.945a.939.939 0 01-.168-.55 1 1 0 01.996-.997h3c.348 0 .649.18.828.45l4.996 7.492c.11.148.168.347.168.55zm0 0",
              }),
            ],
          }),
        });
      }
      const y = "collapseSidebarButton_rEIf",
        I = "collapseSidebarButtonIcon_rjiH";
      function T({ onClick: e }) {
        return (0, b.jsx)("button", {
          type: "button",
          title: (0, c.T)({
            id: "theme.docs.sidebar.collapseButtonTitle",
            message: "Collapse sidebar",
            description:
              "The title attribute for collapse button of doc sidebar",
          }),
          "aria-label": (0, c.T)({
            id: "theme.docs.sidebar.collapseButtonAriaLabel",
            message: "Collapse sidebar",
            description:
              "The title attribute for collapse button of doc sidebar",
          }),
          className: (0, i.A)("button button--secondary button--outline", y),
          onClick: e,
          children: (0, b.jsx)(S, { className: I }),
        });
      }
      var w = a(89749),
        L = a(552);
      const E = Symbol("EmptyContext"),
        B = n.createContext(E);
      function P({ children: e }) {
        const [t, a] = (0, n.useState)(null),
          i = (0, n.useMemo)(
            () => ({ expandedItem: t, setExpandedItem: a }),
            [t],
          );
        return (0, b.jsx)(B.Provider, { value: i, children: e });
      }
      var M = a(62106),
        H = a(79749),
        G = a(48366),
        D = a(19541),
        R = a(72705);
      const W = "menuExternalLink_JE5t",
        V = "linkLabel_Em1w";
      function F({ label: e }) {
        return (0, b.jsx)("span", { title: e, className: V, children: e });
      }
      function Y({
        item: e,
        onItemClick: t,
        activePath: a,
        level: n,
        index: s,
        ...r
      }) {
        const { href: c, label: d, className: u, autoAddBaseUrl: m } = e,
          h = (0, l.w8)(e, a),
          p = (0, D.A)(c);
        return (0, b.jsx)(
          "li",
          {
            className: (0, i.A)(
              o.G.docs.docSidebarItemLink,
              o.G.docs.docSidebarItemLinkLevel(n),
              "menu__list-item",
              u,
            ),
            children: (0, b.jsxs)(_.A, {
              className: (0, i.A)("menu__link", !p && W, {
                "menu__link--active": h,
              }),
              autoAddBaseUrl: m,
              "aria-current": h ? "page" : void 0,
              to: c,
              ...(p && { onClick: t ? () => t(e) : void 0 }),
              ...r,
              children: [
                (0, b.jsx)(F, { label: d }),
                !p && (0, b.jsx)(R.A, {}),
              ],
            }),
          },
          d,
        );
      }
      const U = "categoryLink_P_sm",
        O = "categoryLinkLabel_fGYV";
      function z({ collapsed: e, categoryLabel: t, onClick: a }) {
        return (0, b.jsx)("button", {
          "aria-label": e
            ? (0, c.T)(
                {
                  id: "theme.DocSidebarItem.expandCategoryAriaLabel",
                  message: "Expand sidebar category '{label}'",
                  description: "The ARIA label to expand the sidebar category",
                },
                { label: t },
              )
            : (0, c.T)(
                {
                  id: "theme.DocSidebarItem.collapseCategoryAriaLabel",
                  message: "Collapse sidebar category '{label}'",
                  description:
                    "The ARIA label to collapse the sidebar category",
                },
                { label: t },
              ),
          "aria-expanded": !e,
          type: "button",
          className: "clean-btn menu__caret",
          onClick: a,
        });
      }
      function Q({ label: e }) {
        return (0, b.jsx)("span", { title: e, className: O, children: e });
      }
      function K(e) {
        return 0 === (0, l.Y)(e.item.items, e.activePath).length
          ? (0, b.jsx)(X, { ...e })
          : (0, b.jsx)(q, { ...e });
      }
      function X({ item: e, ...t }) {
        if ("string" != typeof e.href) return null;
        const {
            type: a,
            collapsed: n,
            collapsible: i,
            items: s,
            linkUnlisted: o,
            ...l
          } = e,
          r = { type: "link", ...l };
        return (0, b.jsx)(Y, { item: r, ...t });
      }
      function q({
        item: e,
        onItemClick: t,
        activePath: a,
        level: s,
        index: r,
        ...c
      }) {
        const { items: d, label: u, collapsible: m, className: h, href: p } = e,
          {
            docs: {
              sidebar: { autoCollapseCategories: x },
            },
          } = (0, f.p)(),
          j = (function (e) {
            const t = (0, G.A)();
            return (0, n.useMemo)(
              () =>
                e.href && !e.linkUnlisted
                  ? e.href
                  : !t && e.collapsible
                    ? (0, l.Nr)(e)
                    : void 0,
              [e, t],
            );
          })(e),
          g = (0, l.w8)(e, a),
          v = (0, H.ys)(p, a),
          { collapsed: C, setCollapsed: A } = (0, M.u)({
            initialState: () => !!m && !g && e.collapsed,
          }),
          { expandedItem: k, setExpandedItem: N } = (function () {
            const e = (0, n.useContext)(B);
            if (e === E) throw new L.dV("DocSidebarItemsExpandedStateProvider");
            return e;
          })(),
          S = (e = !C) => {
            (N(e ? null : r), A(e));
          };
        (!(function ({
          isActive: e,
          collapsed: t,
          updateCollapsed: a,
          activePath: i,
        }) {
          const s = (0, L.ZC)(e),
            o = (0, L.ZC)(i);
          (0, n.useEffect)(() => {
            ((e && !s) || (e && s && i !== o)) && t && a(!1);
          }, [e, s, t, a, i, o]);
        })({ isActive: g, collapsed: C, updateCollapsed: S, activePath: a }),
          (0, n.useEffect)(() => {
            m && null != k && k !== r && x && A(!0);
          }, [m, k, r, A, x]));
        return (0, b.jsxs)("li", {
          className: (0, i.A)(
            o.G.docs.docSidebarItemCategory,
            o.G.docs.docSidebarItemCategoryLevel(s),
            "menu__list-item",
            { "menu__list-item--collapsed": C },
            h,
          ),
          children: [
            (0, b.jsxs)("div", {
              className: (0, i.A)("menu__list-item-collapsible", {
                "menu__list-item-collapsible--active": v,
              }),
              children: [
                (0, b.jsx)(_.A, {
                  className: (0, i.A)(U, "menu__link", {
                    "menu__link--sublist": m,
                    "menu__link--sublist-caret": !p && m,
                    "menu__link--active": g,
                  }),
                  onClick: (a) => {
                    (t?.(e),
                      m &&
                        (p
                          ? v
                            ? (a.preventDefault(), S())
                            : S(!1)
                          : (a.preventDefault(), S())));
                  },
                  "aria-current": v ? "page" : void 0,
                  role: m && !p ? "button" : void 0,
                  "aria-expanded": m && !p ? !C : void 0,
                  href: m ? (j ?? "#") : j,
                  ...c,
                  children: (0, b.jsx)(Q, { label: u }),
                }),
                p &&
                  m &&
                  (0, b.jsx)(z, {
                    collapsed: C,
                    categoryLabel: u,
                    onClick: (e) => {
                      (e.preventDefault(), S());
                    },
                  }),
              ],
            }),
            (0, b.jsx)(M.N, {
              lazy: !0,
              as: "ul",
              className: "menu__list",
              collapsed: C,
              children: (0, b.jsx)(te, {
                items: d,
                tabIndex: C ? -1 : 0,
                onItemClick: t,
                activePath: a,
                level: s + 1,
              }),
            }),
          ],
        });
      }
      const Z = "menuHtmlItem_F8gP";
      function J({ item: e, level: t, index: a }) {
        const { value: n, defaultStyle: s, className: l } = e;
        return (0, b.jsx)(
          "li",
          {
            className: (0, i.A)(
              o.G.docs.docSidebarItemLink,
              o.G.docs.docSidebarItemLinkLevel(t),
              s && [Z, "menu__list-item"],
              l,
            ),
            dangerouslySetInnerHTML: { __html: n },
          },
          a,
        );
      }
      function $({ item: e, ...t }) {
        switch (e.type) {
          case "category":
            return (0, b.jsx)(K, { item: e, ...t });
          case "html":
            return (0, b.jsx)(J, { item: e, ...t });
          default:
            return (0, b.jsx)(Y, { item: e, ...t });
        }
      }
      function ee({ items: e, ...t }) {
        const a = (0, l.Y)(e, t.activePath);
        return (0, b.jsx)(P, {
          children: a.map((e, a) =>
            (0, b.jsx)($, { item: e, index: a, ...t }, a),
          ),
        });
      }
      const te = (0, n.memo)(ee),
        ae = "menu_Sk5a",
        ne = "menuWithAnnouncementBar_Uk2V";
      function ie({ path: e, sidebar: t, className: a }) {
        const s = (function () {
          const { isActive: e } = (0, w.M)(),
            [t, a] = (0, n.useState)(e);
          return (
            (0, d.Mq)(
              ({ scrollY: t }) => {
                e && a(0 === t);
              },
              [e],
            ),
            e && t
          );
        })();
        return (0, b.jsx)("nav", {
          "aria-label": (0, c.T)({
            id: "theme.docs.sidebar.navAriaLabel",
            message: "Docs sidebar",
            description: "The ARIA label for the sidebar navigation",
          }),
          className: (0, i.A)("menu thin-scrollbar", ae, s && ne, a),
          children: (0, b.jsx)("ul", {
            className: (0, i.A)(o.G.docs.docSidebarMenu, "menu__list"),
            children: (0, b.jsx)(te, { items: t, activePath: e, level: 1 }),
          }),
        });
      }
      const se = "sidebar_AhiP",
        oe = "sidebarWithHideableNavbar_hbwu",
        le = "sidebarHidden_KXj3",
        re = "sidebarLogo_dDdO";
      function ce({ path: e, sidebar: t, onCollapse: a, isHidden: n }) {
        const {
          navbar: { hideOnScroll: s },
          docs: {
            sidebar: { hideable: o },
          },
        } = (0, f.p)();
        return (0, b.jsxs)("div", {
          className: (0, i.A)(se, s && oe, n && le),
          children: [
            s && (0, b.jsx)(N, { tabIndex: -1, className: re }),
            (0, b.jsx)(ie, { path: e, sidebar: t }),
            o && (0, b.jsx)(T, { onClick: a }),
          ],
        });
      }
      const de = n.memo(ce);
      var ue = a(97612),
        me = a(72489);
      const he = ({ sidebar: e, path: t }) => {
        const a = (0, me.M)();
        return (0, b.jsx)("ul", {
          className: (0, i.A)(o.G.docs.docSidebarMenu, "menu__list"),
          children: (0, b.jsx)(te, {
            items: e,
            activePath: t,
            onItemClick: (e) => {
              ("category" === e.type && e.href && a.toggle(),
                "link" === e.type && a.toggle());
            },
            level: 1,
          }),
        });
      };
      function be(e) {
        return (0, b.jsx)(ue.GX, { component: he, props: e });
      }
      const pe = n.memo(be);
      function xe(e) {
        const t = (0, g.l)(),
          a = "desktop" === t || "ssr" === t,
          n = "mobile" === t;
        return (0, b.jsxs)(b.Fragment, {
          children: [
            a && (0, b.jsx)(de, { ...e }),
            n && (0, b.jsx)(pe, { ...e }),
          ],
        });
      }
      const je = "expandButton_X8OS",
        ge = "expandButtonIcon_QNGC";
      function fe({ toggleSidebar: e }) {
        return (0, b.jsx)("div", {
          className: je,
          title: (0, c.T)({
            id: "theme.docs.sidebar.expandButtonTitle",
            message: "Expand sidebar",
            description:
              "The ARIA label and title attribute for expand button of doc sidebar",
          }),
          "aria-label": (0, c.T)({
            id: "theme.docs.sidebar.expandButtonAriaLabel",
            message: "Expand sidebar",
            description:
              "The ARIA label and title attribute for expand button of doc sidebar",
          }),
          tabIndex: 0,
          role: "button",
          onKeyDown: e,
          onClick: e,
          children: (0, b.jsx)(S, { className: ge }),
        });
      }
      const _e = {
        docSidebarContainer: "docSidebarContainer_QbQ2",
        docSidebarContainerHidden: "docSidebarContainerHidden_Pu6P",
        sidebarViewport: "sidebarViewport_BtBE",
      };
      function ve({ children: e }) {
        const t = (0, r.t)();
        return (0, b.jsx)(n.Fragment, { children: e }, t?.name ?? "noSidebar");
      }
      function Ce({
        sidebar: e,
        hiddenSidebarContainer: t,
        setHiddenSidebarContainer: a,
      }) {
        const { pathname: s } = (0, j.zy)(),
          [l, r] = (0, n.useState)(!1),
          c = (0, n.useCallback)(() => {
            (l && r(!1), !l && (0, x.O)() && r(!0), a((e) => !e));
          }, [a, l]);
        return (0, b.jsx)("aside", {
          className: (0, i.A)(
            o.G.docs.docSidebarContainer,
            _e.docSidebarContainer,
            t && _e.docSidebarContainerHidden,
          ),
          onTransitionEnd: (e) => {
            e.currentTarget.classList.contains(_e.docSidebarContainer) &&
              t &&
              r(!0);
          },
          children: (0, b.jsx)(ve, {
            children: (0, b.jsxs)("div", {
              className: (0, i.A)(
                _e.sidebarViewport,
                l && _e.sidebarViewportHidden,
              ),
              children: [
                (0, b.jsx)(xe, {
                  sidebar: e,
                  path: s,
                  onCollapse: c,
                  isHidden: l,
                }),
                l && (0, b.jsx)(fe, { toggleSidebar: c }),
              ],
            }),
          }),
        });
      }
      const Ae = {
        docMainContainer: "docMainContainer_EIWg",
        docMainContainerEnhanced: "docMainContainerEnhanced_BQjj",
        docItemWrapperEnhanced: "docItemWrapperEnhanced_lacl",
      };
      function ke({ hiddenSidebarContainer: e, children: t }) {
        const a = (0, r.t)();
        return (0, b.jsx)("main", {
          className: (0, i.A)(
            Ae.docMainContainer,
            (e || !a) && Ae.docMainContainerEnhanced,
          ),
          children: (0, b.jsx)("div", {
            className: (0, i.A)(
              "container padding-top--md padding-bottom--lg",
              Ae.docItemWrapper,
              e && Ae.docItemWrapperEnhanced,
            ),
            children: t,
          }),
        });
      }
      const Ne = "docRoot_SYE0",
        Se = "docsWrapper_lRNs";
      function ye({ children: e }) {
        const t = (0, r.t)(),
          [a, i] = (0, n.useState)(!1);
        return (0, b.jsxs)("div", {
          className: Se,
          children: [
            (0, b.jsx)(p, {}),
            (0, b.jsxs)("div", {
              className: Ne,
              children: [
                t &&
                  (0, b.jsx)(Ce, {
                    sidebar: t.items,
                    hiddenSidebarContainer: a,
                    setHiddenSidebarContainer: i,
                  }),
                (0, b.jsx)(ke, { hiddenSidebarContainer: a, children: e }),
              ],
            }),
          ],
        });
      }
      var Ie = a(87564);
      function Te(e) {
        const t = (0, l.B5)(e);
        if (!t) return (0, b.jsx)(Ie.A, {});
        const { docElement: a, sidebarName: n, sidebarItems: c } = t;
        return (0, b.jsx)(s.e3, {
          className: (0, i.A)(o.G.page.docsDocPage),
          children: (0, b.jsx)(r.V, {
            name: n,
            items: c,
            children: (0, b.jsx)(ye, { children: a }),
          }),
        });
      }
    },
    87564(e, t, a) {
      a.d(t, { A: () => l });
      a(10162);
      var n = a(70851),
        i = a(92010),
        s = a(36238),
        o = a(56730);
      function l({ className: e }) {
        return (0, o.jsx)("main", {
          className: (0, n.A)("container margin-vert--xl", e),
          children: (0, o.jsx)("div", {
            className: "row",
            children: (0, o.jsxs)("div", {
              className: "col col--6 col--offset-3",
              children: [
                (0, o.jsx)(s.A, {
                  as: "h1",
                  className: "hero__title",
                  children: (0, o.jsx)(i.A, {
                    id: "theme.NotFound.title",
                    description: "The title of the 404 page",
                    children: "Page Not Found",
                  }),
                }),
                (0, o.jsx)("p", {
                  children: (0, o.jsx)(i.A, {
                    id: "theme.NotFound.p1",
                    description: "The first paragraph of the 404 page",
                    children: "We could not find what you were looking for.",
                  }),
                }),
                (0, o.jsx)("p", {
                  children: (0, o.jsx)(i.A, {
                    id: "theme.NotFound.p2",
                    description: "The 2nd paragraph of the 404 page",
                    children:
                      "Please contact the owner of the site that linked you to the original URL and let them know their link is broken.",
                  }),
                }),
              ],
            }),
          }),
        });
      }
    },
  },
]);
