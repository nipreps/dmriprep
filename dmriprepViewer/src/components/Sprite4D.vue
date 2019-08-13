<template>
  <span class="mt-3">
    <div class="sprite" :id="id" :style="style">
    </div>
  </span>
</template>

<script>
export default {
  name: 'sprite4d',
  computed: {
    row_idx() {
      return Math.floor(this.time / this.M);
    },
    col_idx() {
      return this.time % this.M;
    },
    style() {
      const output = {
        width: `${this.pix}px`,
        height: `${this.pix}px`,
        zoom: 3,
        'background-position-x': `-${this.col_idx * this.pix}px`,
        'background-position-y': `-${this.row_idx * this.pix}px`,
        'background-image': `url('data:image/png;base64,${this.img}')`,
        display: 'inline-flex',
        opacity: this.opacity,
      };
      if (this.overlayMode) {
        output.position = 'absolute';
        output.left = `calc(50% - ${this.pix / 2}px)`;
      }

      return output;
    },
  },
  data() {
    return {

    };
  },
  methods: {

  },
  mounted() {

  },
  watch: {
    time() {

    },
  },
  props: [
    'M', 'N', 'pix', 'num_slices', 'img', 'id', 'time', 'overlayMode', 'opacity',
  ],
};
</script>

<style>
  .sprite {
    background-position: "0px 0px"
  }
</style>
