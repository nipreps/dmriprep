<template>
  <div class="bucket">
    <div class="row">
      <div class="col-md-3">
        <div class="container">
        <h3>{{bucket}} ({{manifestEntries.length}})</h3>
          <div class="mb-3">
            <b-button v-if="!statsReady" @click="getAllReports">
              Compute Statistics
            </b-button>
          </div>
          <b-nav vertical pills class="w-100">
            <!-- <b-nav-item active>Active</b-nav-item> -->
            <b-nav-item v-for="(subject, index) in manifestEntries"
             :key="subject" :active="index === currentReportIdx"
             @click="currentReportIdx = index">
              {{subject.split('/')[0]}}
            </b-nav-item>
          </b-nav>
        </div>
      </div>
      <div class="col-md-9">
        <h1 v-if="manifestEntries.length">
          {{manifestEntries[currentReportIdx].split('/')[0]}}
        </h1>
        <div v-if="statsReady">
          <GroupStats :data="allReports" :individual="currentReport.eddy_quad"/>
        </div>
        <div v-if="ready">
          <report
            :reportProp="currentReport"
          />
        </div>
        <div v-else>
          loading...
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import _ from 'lodash';
import Report from './Report';
import GroupStats from './GroupStats';

export default {
  name: 'bucket',
  data() {
    return {
      manifestEntries: [],
      currentReportIdx: 0,
      currentReport: {},
      ready: false,
      allReports: [],
      statsReady: false,
    };
  },
  components: {
    Report,
    GroupStats,
  },
  methods: {
    getReport(r) {
      return axios.get(`https://s3-us-west-2.amazonaws.com/${this.bucket}/${r}`);
    },
    /**
    *
    */
    async getAllReports() {
      this.statsReady = false;
      const reports = await _.map(this.manifestEntries, m => this.getReport(m));
      _.map(reports, (r) => {
        r.then((resp) => {
          if (resp.data.eddy_quad) {
            this.allReports.push(resp.data.eddy_quad);
          }
        });
      });
      this.statsReady = true;
    },
    /**
    * XML parser for pubmed query returns.
    */
    xmlParser(input) {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(input, 'text/xml');
      return xmlDoc;
    },
    /**
    *
    */
    parseS3(data) {
      const xml = this.xmlParser(data);
      const keys = xml.getElementsByTagName('Key');
      const continuation = xml.getElementsByTagName('NextContinuationToken');
      const isTruncated = xml.getElementsByTagName('IsTruncated')[0].innerHTML;
      if (isTruncated === 'true') {
        this.continuation = encodeURIComponent(continuation[0].innerHTML);
      } else {
        this.continuation = null;
      }
      const allKeys = _.map(keys, k => k.innerHTML);
      const reportsFiltered = _.filter(allKeys, k => k.endsWith('_report.json'));// _.map(allKeys, k => k.split('/')[0]);
      const keysFixed = _.uniq(reportsFiltered);
      return keysFixed;
    },
    /**
    * if there is a continuation token..
    */
    S3Continuation(token) {
      let url = `https://s3-us-west-2.amazonaws.com/${this.bucket}/?list-type=2&`;
      // url += `prefix=${this.config.manifestS3.prefix}/&max-keys=100000`;
      url += '&max-keys=100000';
      // url += `&delimiter=${this.config.manifestS3.delimiter}`;
      url += `&continuation-token=${token}`;
      if (!token) {
        return 0;
      }
      return axios.get(url).then((resp) => {
        const keysFixed2 = this.parseS3(resp.data);
        this.manifestEntries = _.uniq(this.manifestEntries.concat(keysFixed2));
        if (this.continuation) {
          this.S3Continuation(this.continuation);
        }
      });
    },
    /**
    * get a list of files that are in a bucket of an S3
    * with a prefix and a delimiter (usually, a .)
    * TODO: make the keys firebase safe!!
    */
    getS3Manifest() {
      let url = `https://s3-us-west-2.amazonaws.com/${this.bucket}/?list-type=2&`;
      url += '&max-keys=100000';
      // url += `prefix=${this.config.manifestS3.prefix}
      // /&max-keys=${this.config.manifestS3.max_keys}`;
      // url += `&delimiter=${this.config.manifestS3.delimiter}`;
      // console.log(url);
      return axios.get(url).then((resp) => {
        const keysFixed = this.parseS3(resp.data);
        this.manifestEntries = _.uniq(this.manifestEntries.concat(keysFixed));
        if (this.continuation) {
          this.S3Continuation(this.continuation);
        }
      });
    },
    updateReport() {
      this.ready = false;
      const reportUrl = `https://s3-us-west-2.amazonaws.com/${this.bucket}/${this.manifestEntries[this.currentReportIdx]}`;
      return axios.get(reportUrl)
        .then((resp) => {
          this.currentReport = resp.data;
          this.ready = true;
          this.$router.replace({ name: 'Bucket',
            params: { bucket: this.bucket },
            query: { report: reportUrl } });
        });
    },
  },
  computed: {
    bucket() {
      return this.$route.params.bucket;
    },
  },
  watch: {
    bucket() {
      this.getS3Manifest();
    },
    currentReportIdx() {
      this.updateReport();
    },
  },
  mounted() {
    let path = null;
    if (this.$route.query) {
      if (this.$route.query.report) {
        path = this.$route.query.report.split(`https://s3-us-west-2.amazonaws.com/${this.bucket}/`)[1];
      }
    }

    this.getS3Manifest().then(this.updateReport).then(() => {
      if (path) {
        this.currentReportIdx = this.manifestEntries.indexOf(path);
      }
      this.getAllReports();
    });
  },
};
</script>

<style>

</style>
