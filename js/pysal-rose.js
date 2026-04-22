function renderRosePlot(payload, rootId) {
  const root = document.getElementById(rootId);
  root.innerHTML = `
    <div class="container">
      <div class="controls">
        <h2>Interactive Controls</h2>

        <div class="slider-container">
          <label for="${rootId}-scale-factor">Scale Factor: <span id="${rootId}-scale-value">0.9</span></label>
          <input type="range" id="${rootId}-scale-factor" min="0.5" max="2.0" step="0.1" value="0.9" style="width:100%;">
        </div>

        <div class="slider-container">
          <label for="${rootId}-line-width">Line Width: <span id="${rootId}-line-width-value">2.5</span></label>
          <input type="range" id="${rootId}-line-width" min="0.5" max="5.0" step="0.1" value="2.5" style="width:100%;">
        </div>

        <div class="slider-container">
          <label for="${rootId}-opacity">Opacity: <span id="${rootId}-opacity-value">0.8</span></label>
          <input type="range" id="${rootId}-opacity" min="0.1" max="1.0" step="0.1" value="0.8" style="width:100%;">
        </div>

        <button id="${rootId}-reset-view" class="control-button">Reset View</button>

        <p class="help-text">
          <strong>Scale Factor:</strong> Adjusts the overall size of all module polygons<br>
          <strong>Line Width:</strong> Controls polygon outline thickness<br>
          <strong>Opacity:</strong> Changes transparency of lines and points<br>
          <strong>Hover:</strong> Hover over markers or lines to view raw module data
        </p>

        <p class="help-text" id="${rootId}-updated-at"></p>
        <p id="${rootId}-error-message" class="error-message">An error occurred while rendering the plot.</p>
      </div>

      <div class="chart">
        <h2>PySAL Ecosystem: Multi-Dimensional Performance Rose Plot</h2>
        <svg id="${rootId}-rose-plot" width="100%" height="600"></svg>
      </div>

      <div class="legend">
        <h2>PySAL Modules</h2>
        <p class="help-text">Click module buttons to show or hide sub-modules.</p>
        <div id="${rootId}-module-legend"></div>
      </div>

      <div class="metrics">
        <h2>Performance Metrics Overview</h2>
        <p id="${rootId}-metrics-content" class="help-text"></p>
      </div>
    </div>

    <div class="tooltip" id="${rootId}-tooltip" style="display:none;"></div>
  `;

  const rawData = payload.data;
  document.getElementById(`${rootId}-updated-at`).textContent = "Last updated: " + payload.generated_at_utc;

  const totalPypiLastMonth = payload.totals.pypi_last_month_total;
  const totalConda = payload.totals.conda_total_downloads_total;
  const featureLabels = payload.feature_labels;

  const modules = rawData.map(d => ({
    name: d.module,
    values: d.values,
    raw: d,
    color: d.color,
    visible: d.visible,
    pypi_rank: d.pypi_rank,
    conda_rank: d.conda_rank,
    size: d.size
  }));

  const width = 600;
  const height = 600;
  const radius = Math.min(width, height) / 2 - 50;

  const svgRoot = d3.select(`#${rootId}-rose-plot`).attr("viewBox", `0 0 ${width} ${height}`);
  const svg = svgRoot.append("g").attr("transform", `translate(${width / 2}, ${height / 2})`);

  const numVars = featureLabels.length;
  const angleSlice = 2 * Math.PI / numVars;
  const angles = d3.range(numVars).map(i => i * angleSlice);

  const getX = (angle, r) => r * Math.cos(angle - Math.PI / 2);
  const getY = (angle, r) => r * Math.sin(angle - Math.PI / 2);

  let scaleFactor = 0.9;
  let lineWidth = 2.5;
  let opacity = 0.8;

  const tooltip = d3.select(`#${rootId}-tooltip`);

  function showTooltip(event, module) {
    const raw = module.raw;
    const pypiPct = totalPypiLastMonth ? (raw.pypi_last_month / totalPypiLastMonth * 100).toFixed(2) : "0.00";
    const condaPct = totalConda ? (raw.conda_total_downloads / totalConda * 100).toFixed(2) : "0.00";

    const content = `
      <strong>${module.name}</strong><br>
      PyPI Install (Last week): ${Number(raw.pypi_last_week).toLocaleString()}<br>
      PyPI Install (Last month): ${Number(raw.pypi_last_month).toLocaleString()} (${pypiPct}%, Rank: ${module.pypi_rank}/${rawData.length})<br>
      Conda Install (Total): ${Number(raw.conda_total_downloads).toLocaleString()} (${condaPct}%, Rank: ${module.conda_rank}/${rawData.length})<br>
      GitHub Stars: ${Number(raw.stars).toLocaleString()}<br>
      GitHub Forks: ${Number(raw.forks).toLocaleString()}<br>
      Age (Years): ${Number(raw.age_years).toFixed(1)}<br>
      Contributors: ${Number(raw.contributors).toLocaleString()}<br>
      Repo: <a href="${raw.repo_url}" target="_blank">GitHub</a><br>
      PyPI: <a href="${raw.pypi_url}" target="_blank">Package</a><br>
      Conda: <a href="${raw.conda_url}" target="_blank">Package</a>
    `;

    tooltip.html(content)
      .style("left", `${event.pageX + 10}px`)
      .style("top", `${event.pageY - 10}px`)
      .style("display", "block");
  }

  function hideTooltip() {
    tooltip.style("display", "none");
  }

  function updateMetricsPanel() {
    const s = payload.summary;
    document.getElementById(`${rootId}-metrics-content`).innerHTML =
      `• Total Modules: ${s.total_modules}<br>` +
      `• Top PIP Install (Last month): ${s.top_pypi_month} (${Number(s.top_pypi_month_value).toLocaleString()})<br>` +
      `• Top Conda Install (Total): ${s.top_conda_total} (${Number(s.top_conda_total_value).toLocaleString()})<br>` +
      `• Most Starred: ${s.most_starred} (${Number(s.most_starred_value).toLocaleString()} stars)<br>` +
      `• Oldest Module: ${s.oldest_module} (${Number(s.oldest_module_value).toFixed(1)} years)`;
  }

  function drawPlot() {
    try {
      svg.selectAll("*").remove();
      const currentRadius = radius * scaleFactor;

      [0.2, 0.4, 0.6, 0.8, 1.0].forEach(level => {
        svg.append("circle")
          .attr("r", currentRadius * level)
          .attr("fill", "none")
          .attr("stroke", "gray")
          .attr("stroke-width", 0.8)
          .attr("opacity", 0.3);
      });

      svg.selectAll(".level-label")
        .data([0.2, 0.4, 0.6, 0.8, 1.0])
        .join("text")
        .attr("class", "level-label")
        .attr("x", -currentRadius - 10)
        .attr("y", d => -currentRadius * d)
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .attr("font-size", 10)
        .attr("opacity", 0.8)
        .text(d => d.toFixed(1));

      svg.selectAll(".axisLine")
        .data(angles)
        .join("line")
        .attr("class", "axisLine")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", d => getX(d, currentRadius))
        .attr("y2", d => getY(d, currentRadius))
        .attr("stroke", "gray")
        .attr("stroke-width", 1);

      svg.selectAll(".axisLabel")
        .data(featureLabels)
        .join("text")
        .attr("class", "axisLabel")
        .attr("x", (d, i) => getX(angles[i], currentRadius * 1.3))
        .attr("y", (d, i) => {
          let y = getY(angles[i], currentRadius * 1.3);
          if (Math.sin(angles[i] - Math.PI / 2) > 0) y += 18;
          return y;
        })
        .attr("dy", ".35em")
        .attr("text-anchor", (d, i) => {
          const a = angles[i] - Math.PI / 2;
          return Math.cos(a) > 0.15 ? "start" : Math.cos(a) < -0.15 ? "end" : "middle";
        })
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .each(function(d) {
          const text = d3.select(this);
          const lines = d.split("\n");
          text.text(null);
          lines.forEach((line, idx) => {
            text.append("tspan")
              .attr("x", text.attr("x"))
              .attr("dy", idx === 0 ? 0 : "1.1em")
              .text(line);
          });
        });

      const visibleModules = modules.filter(d => d.visible).sort((a, b) => b.size - a.size);

      visibleModules.forEach(module => {
        const dataPoints = module.values.map((v, i) => ({
          angle: angles[i],
          value: v
        }));

        const lineGen = d3.line()
          .x(p => getX(p.angle, p.value * currentRadius))
          .y(p => getY(p.angle, p.value * currentRadius))
          .defined(p => isFinite(p.value));

        const group = svg.append("g");

        group.append("path")
          .attr("d", lineGen(dataPoints) + "Z")
          .attr("fill", module.color)
          .attr("fill-opacity", 0.2)
          .attr("stroke", "none")
          .on("mouseover", event => showTooltip(event, module))
          .on("mousemove", event => showTooltip(event, module))
          .on("mouseout", hideTooltip);

        group.append("path")
          .attr("d", lineGen(dataPoints) + "Z")
          .attr("fill", "none")
          .attr("stroke", module.color)
          .attr("stroke-width", lineWidth + 1)
          .attr("opacity", 0.4)
          .on("mouseover", event => showTooltip(event, module))
          .on("mousemove", event => showTooltip(event, module))
          .on("mouseout", hideTooltip);

        group.append("path")
          .attr("d", lineGen(dataPoints) + "Z")
          .attr("fill", "none")
          .attr("stroke", module.color)
          .attr("stroke-width", lineWidth)
          .attr("opacity", 0.9)
          .on("mouseover", event => showTooltip(event, module))
          .on("mousemove", event => showTooltip(event, module))
          .on("mouseout", hideTooltip);

        group.selectAll("circle")
          .data(dataPoints)
          .join("circle")
          .attr("cx", p => getX(p.angle, p.value * currentRadius))
          .attr("cy", p => getY(p.angle, p.value * currentRadius))
          .attr("r", 5)
          .attr("fill", module.color)
          .attr("opacity", opacity)
          .on("mouseover", event => showTooltip(event, module))
          .on("mousemove", event => showTooltip(event, module))
          .on("mouseout", hideTooltip);
      });
    } catch (error) {
      console.error("Error rendering plot:", error);
      d3.select(`#${rootId}-error-message`).style("display", "block");
    }
  }

  const legend = d3.select(`#${rootId}-module-legend`)
    .selectAll("button")
    .data(modules)
    .join("button")
    .attr("class", "module-button")
    .on("click", function(event, d) {
      d.visible = !d.visible;
      d3.select(this).selectAll("span").style("opacity", d.visible ? 1 : 0.3);
      drawPlot();
    });

  legend.append("span")
    .attr("class", "module-swatch")
    .style("background-color", d => d.color)
    .style("opacity", d => d.visible ? 1 : 0.3);

  legend.append("span")
    .text(d => d.name)
    .style("opacity", d => d.visible ? 1 : 0.3);

  d3.select(`#${rootId}-scale-factor`).on("input", function() {
    scaleFactor = +this.value;
    d3.select(`#${rootId}-scale-value`).text(scaleFactor.toFixed(1));
    drawPlot();
  });

  d3.select(`#${rootId}-line-width`).on("input", function() {
    lineWidth = +this.value;
    d3.select(`#${rootId}-line-width-value`).text(lineWidth.toFixed(1));
    drawPlot();
  });

  d3.select(`#${rootId}-opacity`).on("input", function() {
    opacity = +this.value;
    d3.select(`#${rootId}-opacity-value`).text(opacity.toFixed(1));
    drawPlot();
  });

  d3.select(`#${rootId}-reset-view`).on("click", () => {
    scaleFactor = 0.9;
    lineWidth = 2.5;
    opacity = 0.8;
    modules.forEach(d => d.visible = false);
    const pysalModule = modules.find(d => d.name === "pysal");
    if (pysalModule) pysalModule.visible = true;

    d3.select(`#${rootId}-scale-factor`).property("value", scaleFactor);
    d3.select(`#${rootId}-scale-value`).text(scaleFactor.toFixed(1));
    d3.select(`#${rootId}-line-width`).property("value", lineWidth);
    d3.select(`#${rootId}-line-width-value`).text(lineWidth.toFixed(1));
    d3.select(`#${rootId}-opacity`).property("value", opacity);
    d3.select(`#${rootId}-opacity-value`).text(opacity.toFixed(1));

    d3.select(`#${rootId}-module-legend`).selectAll("span").style("opacity", d => d.visible ? 1 : 0.3);
    drawPlot();
  });

  updateMetricsPanel();
  drawPlot();
}
