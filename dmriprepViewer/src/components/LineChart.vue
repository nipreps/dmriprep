<template>
  <svg ref="chart" :id="id" class="lineChart"></svg>
</template>

<script>
const d3 = require('d3');

window.d3 = d3;

export default {
  name: 'lineChart',
  data() {
    return {
      svg: null,
      g: null,
      x: null,
      y: null,
      xDomain: [0, 1],
      yDomain: [0, 1],
      margin: { top: 20, right: 20, bottom: 30, left: 50 },
      lines: [],
    };
  },
  computed: {
    width() {
      return this.$refs.chart.clientWidth - this.margin.left - this.margin.right;
    },
    height() {
      return this.$refs.chart.clientHeight - this.margin.top - this.margin.bottom;
    },
  },
  watch: {
    highlightIdx() {
      // console.log('watching', this.highlightIdx)
      this.updateHighlightPoints();
    },
  },
  methods: {
    initAx() {
      // console.log(this.$refs.chart.clientWidth);
      const svg = d3.select(`#${this.id}`);

      // const width = this.$refs.chart.clientWidth - margin.left - margin.right
      // const height = this.$refs.chart.clientHeight - margin.top - margin.bottom
      const g = svg.append('g').attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
      const y = d3.scaleLinear()
        .range([this.height, 0]);
      const x = d3.scaleLinear()
        .range([0, this.width]);

      this.svg = svg;
      this.g = g;
      this.x = x;
      this.y = y;

      this.initXaxis();
      this.initYaxis();
      this.initHighlightPoints();
    },
    initXaxis() {
      this.g.append('g')
        .attr('class', 'x axis')
        .attr('transform', `translate(0, ${this.height})`)
        .call(d3.axisBottom(this.x));
      // this.updateXaxis();
    },
    updateXaxis() {
      this.x.range([0, this.width]).domain(this.xDomain);
      d3.select(`#${this.id} .x.axis`).call(d3.axisBottom(this.x));
    },
    initYaxis() {
      this.g.append('g')
        .attr('class', 'y axis')
        .call(d3.axisLeft(this.y))
        .append('text')
        .attr('fill', '#000')
        .attr('transform', 'rotate(-90)')
        .attr('y', 6)
        .attr('dy', '0.71em')
        .attr('text-anchor', 'end')
        .text(this.ylabel);
      // this.updateYaxis();
    },
    updateYaxis() {
      this.y.range([this.height, 0]).domain(this.yDomain);
      d3.select(`#${this.id} .y.axis`).call(d3.axisLeft(this.y));
    },
    initHighlightPoints() {
      this.g.append('circle').attr('class', 'dot-series-1');
      this.g.append('circle').attr('class', 'dot-series-2');
    },
    updateHighlightPoints() {
      const self = this;
      d3.select(`#${this.id} .dot-series-1`)
        .attr('r', 7)
        .attr('cx', () => self.x(self.highlightIdx))
        .attr('cy', () => self.y(self.data[self.highlightIdx][0]))
        .attr('fill', 'steelblue');

      d3.select(`#${this.id} .dot-series-2`)
        .attr('r', 7)
        .attr('cx', () => self.x(self.highlightIdx))
        .attr('cy', () => self.y(self.data[self.highlightIdx][1]))
        .attr('fill', 'red');
    },
    plotData() {
      const self = this;

      /* eslint-disable */
      const minX = d3.min(this.data, function g(d, i) { return i; });
      const maxX = d3.max(this.data, function g(d, i) { return i; });

      const maxY = d3.max(this.data, function g(d, i) { return d3.max(d); });
      const minY = d3.min(this.data, function g(d, i) { return d3.min(d); });
      /* eslint-enable */

      this.xDomain = [minX, maxX];
      this.yDomain = [minY, maxY];

      this.updateXaxis();
      this.updateYaxis();

      /* eslint-disable */
      const line1 = d3.line()
             .x(function f(d, i) { return self.x(i); })
             .y(function f(d, i) { return self.y(d[0]); });

      const line2 = d3.line()
             .x(function f(d, i) { return self.x(i); })
             .y(function f(d, i) { return self.y(d[1]); });
      /* eslint-enable */

      this.lines = [line1, line2];


      this.g.append('path')
        .attr('class', 'series-1')
        .datum(this.data)
        .attr('fill', 'none')
        .attr('stroke', 'steelblue')
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round')
        .attr('stroke-width', 1.5)
        .attr('d', line1);

      this.g.append('path')
        .attr('class', 'series-2')
        .datum(this.data)
        .attr('fill', 'none')
        .attr('stroke', 'red')
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round')
        .attr('stroke-width', 1.5)
        .attr('d', line2);

      this.g.selectAll('.outlier')
        .data(this.outlier_indices)
        .enter()
        .append('rect')
        .attr('class', 'outlier')
        .attr('x', i => self.x(i) - 1.5)
        .attr('y', () => self.y(maxY))
        .attr('width', '3px')
        .attr('height', () => `${self.height}px`)
        .attr('fill', 'black');


      this.svg.on('mousemove', () => {
        // const x0 = self.x.invert(d3.mouse(this)[0]);
        // const bisect = d3.bisector(function(d){return d[0]}).left;
        // window.bisect = bisect;
        // console.log(x0, self.x(0));
      });
    },


  },
  mounted() {
    this.initAx();
    this.plotData();
  },
  props: ['ylabel', 'xlabel', 'data', 'id', 'highlightIdx', 'outlier_indices'],
};
</script>

<style>
  .lineChart {
    width: 100%;
    height: 100%;
  }
</style>
