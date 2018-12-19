<template>
  <div class="mt-3 container">
    <div v-if="report">
      <h2 class="mt-3 pt-3">Corrected dwi</h2>
      <p class="lead">Result of eddy</p>

      <sprite4d v-for="view in report.dwi_corrected"
                :key="view.orientation"
                :M="view.M"
                :N="view.N"
                :img="view.img"
                :num_slices="view.num_slices"
                :pix="view.pix"
                :id="view.orientation"
                :time="time"
                :overlayMode="false"
                opacity="1"
      >
      </sprite4d>
      <vue-slider ref="timeSlider" v-model="time"
       :min="0" :max="report.dwi_corrected[0].num_slices-1">
     </vue-slider>
      <h2 class="mt-3 pt-3">Eddy Report</h2>
      <p class="lead"> <b-btn v-b-toggle.collapse1 variant="primary">
        Outliers ({{report.eddy_report.length}})</b-btn> </p>
        <b-collapse id="collapse1" class="mt-2">
          <b-card>

            <p v-for="e in report.eddy_report" :key="e">{{e}}</p>

          </b-card>
        </b-collapse>

        <div style="height: 200px; width: 100%; display: inline-flex;">
          <line-chart id="motion_params"
           :data="report.eddy_params"
           :outlier_indices="report.outlier_volumes"
           xlabel="TR"
           ylabel="RMS"
           :highlightIdx="time"
          >
          </line-chart>
        </div>

      <h2 class="mt-3 pt-3">Registration + Brain Mask</h2>
      <p class="lead">Brain mask computed on T1w, and mapped to B0</p>

      <BrainSprite
        id="brainMaskSprite"
        ref="brainMaskSprite"
        :base_dim_x="report.b0.pix"
        :base_dim_y="report.b0.pix"
        :overlay_dim_x="report.anat_mask.pix"
        :overlay_dim_y="report.anat_mask.pix"
        :base="report.b0.img"
        :overlay="report.anat_mask.img"
      />

      <h2 class="mt-3 pt-3">DTI: ColorFA</h2>
      <p class="lead">Color FA mapped on B0</p>

      <BrainSprite
        id="colorFASprite"
        ref="colorFASprite"
        :base_dim_x="report.b0.pix"
        :base_dim_y="report.b0.pix"
        :overlay_dim_x="report.colorFA.pix"
        :overlay_dim_y="report.colorFA.pix"
        :base="report.b0.img"
        :overlay="report.colorFA.img"
      />

    </div>
  </div>
</template>

<script>
import axios from 'axios';
import vueSlider from 'vue-slider-component';
import sprite4d from './Sprite4D';
import lineChart from './LineChart';
import BrainSprite from './BrainSprite.vue';

export default {
  name: 'report',
  components: {
    sprite4d,
    vueSlider,
    lineChart,
    BrainSprite,
  },
  data() {
    return {
      time: 0,
      spriteSlice: 0,
      report: null,
    };
  },
  methods: {
    get_mid_slice() {
      return Math.floor(this.report.b0.num_slices / 2);
    },
  },
  created() {
    // console.log('in created', this.$route.query);
    if (this.$route.query) {
      // load the json
      if (!this.$route.query.url && this.$route.name === 'Report') {
        this.$router.push('/');
      } else if (this.$route.query.url) {
        axios.get(this.$route.query.url).then((resp) => {
          this.report = resp.data;
        });
      }
    }
  },
  mounted() {
    if (this.reportProp) {
      this.report = this.reportProp;
    }
    this.$nextTick(() => {
      if (this.report) {
        this.spriteSlice = this.get_mid_slice();
        // this.$refs.brainMaskSprite.initBrainSprite();
        // this.$refs.colorFASprite.initBrainSprite();
      }
    });
  },
  watch: {
    reportProp() {
      if (this.reportProp) {
        this.report = this.reportProp;
      }
    },
    report() {
      if (this.report) {
        this.spriteSlice = this.get_mid_slice();
      }
    },
    $route() {
      if (this.$route.query) {
        // load the json
        if (!this.$route.query.url && this.$route.name === 'Report') {
          this.$router.push('/');
        } else {
          console.log('getting axios?', this.$route.query.url);
          axios.get(this.$route.query.url).then((resp) => {
            this.report = resp.data;
          });
        }
      }
    },
  },
  props: {
    reportProp: Object,
  },
};
</script>

<style>

</style>
