<template>
  <b-container>
      <img class="logo" src="../assets/logo.svg" />
      <h1>dmriprep Viewer</h1>
      <p class="lead">Upload your report.json file from dmriprep</p>
      <b-form-file class="mt-3" v-model="file"
       :state="Boolean(file)" placeholder="Choose a file...">
     </b-form-file>

     <p class="lead mt-3">OR copy/paste a URL</p>
     <b-input-group size="md" class="mb-3" prepend="URL">
        <b-form-input v-model="url" />
        <b-input-group-append>
          <b-btn size="md" text="Button"
           variant="primary"
           @click="navigate">Go</b-btn>
        </b-input-group-append>
      </b-input-group>

      <p class="lead mt-3">OR point to an S3 bucket</p>
      <b-input-group size="md" class="mb-3" prepend="Bucket">
         <b-form-input v-model="bucket" />
         <b-input-group-append>
           <b-btn size="md" text="Button"
            variant="primary"
            @click="s3">Go</b-btn>
         </b-input-group-append>
       </b-input-group>

      <report v-if="report.b0" :reportProp="report"></report>
  </b-container>
</template>

<script>
import vueSlider from 'vue-slider-component';
import sprite4d from './Sprite4D';
import lineChart from './LineChart';
import report from './Report';


export default {
  name: 'HelloWorld',
  components: {
    sprite4d,
    vueSlider,
    lineChart,
    report,
  },
  data() {
    return {
      file: null,
      msg: 'Welcome to Your Vue.js App',
      report: {},
      time: 0,
      spriteSlice: 0,
      url: null,
      bucket: null,
    };
  },
  methods: {
    get_mid_slice() {
      return Math.floor(this.report.b0.num_slices / 2);
    },
    navigate() {
      this.$router.push({ path: '/report', query: { url: this.url } });
    },
    s3() {
      this.$router.push({ path: `/bucket/${this.bucket}` });
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
