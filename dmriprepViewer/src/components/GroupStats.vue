<template>
  <div>
    <div class="mb-3">
      <p class="lead">
        Comparison to Group Eddy_Quad Statistics
      </p>
      <p>Absolute Motion (Z = {{numberFormatter(individual_abs_mot_z)}})</p>
      <b-progress class="w-50 mx-auto">
        <b-progress-bar :value="scaleZ(individual_abs_mot_z)"
         :variant="getColor(0, individual_abs_mot_z)">
          z = {{numberFormatter(individual_abs_mot_z)}}
        </b-progress-bar>
      </b-progress>
    </div>
    <div class="mb-3">
      <p>Relative Motion (Z = {{numberFormatter(individual_rel_mot_z)}})</p>
      <b-progress class="w-50 mx-auto">
        <b-progress-bar :value="scaleZ(individual_rel_mot_z)"
         :variant="getColor(0, individual_rel_mot_z)">
          z = {{numberFormatter(individual_rel_mot_z)}}
        </b-progress-bar>
      </b-progress>
    </div>

  </div>
</template>

<script>
// import _ from 'lodash';
const d3 = require('d3');

export default {
  name: 'GroupStats',
  props: ['data', 'individual'],
  data() {
    return {

    };
  },
  methods: {
    scaleZ(val) {
      const scaler = d3.scaleLinear().range([0, 100]).domain([-3, 3]);
      return scaler(val);
    },
    numberFormatter(val) {
      const formatter = d3.format('.3n');
      return formatter(val);
    },
    getColor(direction, zScore) {
      if (direction) {
        // positive is good
        if (zScore <= -1) {
          return 'danger';
        } else if (zScore >= 1) {
          return 'success';
        }
      }
      if (zScore <= -1) {
        return 'success';
      } else if (zScore >= 1) {
        return 'danger';
      }
      return 'primary';
    },
  },
  computed: {
    mean_group_abs_mot() {
      return d3.mean(this.data, d => d.qc_mot_abs);
    },
    std_group_abs_mot() {
      return d3.deviation(this.data, d => d.qc_mot_abs);
    },
    individual_abs_mot_z() {
      if (this.individual) {
        return (this.individual.qc_mot_abs - this.mean_group_abs_mot) / this.std_group_abs_mot;
      }
      return null;
    },
    mean_group_rel_mot() {
      return d3.mean(this.data, d => d.qc_mot_rel);
    },
    std_group_rel_mot() {
      return d3.deviation(this.data, d => d.qc_mot_rel);
    },
    individual_rel_mot_z() {
      if (this.individual) {
        return (this.individual.qc_mot_rel - this.mean_group_rel_mot) / this.std_group_rel_mot;
      }
      return null;
    },
  },
};
</script>

<style>
</style>
