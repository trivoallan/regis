"use strict";
(globalThis.webpackChunk_regis_dashboard =
  globalThis.webpackChunk_regis_dashboard || []).push([
  [9139],
  {
    59139(a, e, r) {
      r.d(e, { diagram: () => o });
      var s = r(59991),
        t = r(69623),
        n = r(94553),
        d = r(3733),
        i = { version: "11.13.0" },
        o = {
          parser: {
            parse: (0, n.K2)(async (a) => {
              const e = await (0, d.qg)("info", a);
              n.Rm.debug(e);
            }, "parse"),
          },
          db: { getVersion: (0, n.K2)(() => i.version, "getVersion") },
          renderer: {
            draw: (0, n.K2)((a, e, r) => {
              n.Rm.debug("rendering info diagram\n" + a);
              const d = (0, s.D)(e);
              (0, t.a$)(d, 100, 400, !0);
              d.append("g")
                .append("text")
                .attr("x", 100)
                .attr("y", 40)
                .attr("class", "version")
                .attr("font-size", 32)
                .style("text-anchor", "middle")
                .text(`v${r}`);
            }, "draw"),
          },
        };
    },
  },
]);
