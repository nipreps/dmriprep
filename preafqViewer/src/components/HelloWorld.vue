<template>
  <b-container>
      <img class="logo" src="../assets/logo.svg" />
      <h1>preAFQ Viewer</h1>
      <p class="lead">Upload your report.json file from preAFQ</p>
      <b-form-file class="mt-3" v-model="file"
       :state="Boolean(file)" placeholder="Choose a file...">
     </b-form-file>
      <div v-if="report.b0" class="mt-3">
        <h2 class="mt-3 pt-3">Corrected dwi</h2>
        <p class="lead">Result of eddy</p>
        <vue-slider ref="timeSlider" v-model="time"
         :min="0" :max="report.dwi_corrected[0].num_slices-1">
       </vue-slider>
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
             xlabel="TR"
             ylabel="RMS"
             :highlightIdx="time"
            >
            </line-chart>
          </div>

        <h2 class="mt-3 pt-3">Registration + Brain Mask</h2>
        <p class="lead">Brain mask computed on T1w, and mapped to B0</p>

        <sprite4d
          :key="'bmask'+2"
          :M="report.b0.M"
          :N="report.b0.N"
          :num_slices="report.b0.num_slices"
          id="b0_mask"
          :pix="report.b0.pix"
          :time="spriteSlice"
          :img="report.b0.img"
          opacity="1"
        ></sprite4d>
        <sprite4d
          :key="'anat_mask'+1"
          :M="report.anat_mask.M"
          :N="report.anat_mask.N"
          :num_slices="report.anat_mask.num_slices"
          id="anat_mask"
          :pix="report.anat_mask.pix"
          :time="spriteSlice"
          :img="report.anat_mask.img"
          :overlayMode="true"
          opacity="1"
        ></sprite4d>
        <vue-slider ref="timeSlider"
         v-model="spriteSlice" :min="0"
         :max="report.b0.num_slices-1"></vue-slider>

        <h2 class="mt-3 pt-3">DTI: ColorFA</h2>
        <p class="lead">Color FA mapped on B0</p>

        <sprite4d
          key="bmask1"
          :M="report.b0.M"
          :N="report.b0.N"
          :num_slices="report.b0.num_slices"
          id="b0_mask"
          :pix="report.b0.pix"
          :time="spriteSlice"
          :img="report.b0.img"
          opacity="1"
        ></sprite4d>
        <sprite4d
          key="colorfa_mask"
          :M="report.colorFA.M"
          :N="report.colorFA.N"
          :num_slices="report.colorFA.num_slices"
          id="colorfa_mask"
          :pix="report.colorFA.pix"
          :time="spriteSlice"
          :img="report.colorFA.img"
          :overlayMode="true"
          opacity="0.5"
        ></sprite4d>

      </div>
  </b-container>
</template>

<script>
import vueSlider from 'vue-slider-component';
import sprite4d from './Sprite4D';
import lineChart from './LineChart';

export default {
  name: 'HelloWorld',
  components: {
    sprite4d,
    vueSlider,
    lineChart,
  },
  data() {
    return {
      file: null,
      msg: 'Welcome to Your Vue.js App',
      report: {},
      time: 0,
      spriteSlice: 0,
    };
  },
  methods: {
    get_mid_slice() {
      return Math.floor(this.report.b0.num_slices / 2);
    },
  },
  watch: {
    file() {
      if (this.file) {
        const reader = new FileReader();
        const self = this;
        reader.onload = function Load(e) {
          const contents = e.target.result;
          self.report = JSON.parse(contents);
          // console.log(self.report);
        };
        reader.readAsText(this.file);
      }
    },
    report() {
      if (this.report.b0) {
        this.spriteSlice = this.get_mid_slice();
      }
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

.logo {
  max-width: 300px;
}

h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
