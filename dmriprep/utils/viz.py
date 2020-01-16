import numpy as np
import nibabel as nb
from skimage import measure
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def scaled_mip(img1, img2, img3, axis):
    mip1 = img1.max(axis=axis).T
    mip2 = img2.max(axis=axis).T
    mip3 = img3.max(axis=axis).T
    max_obs = max(mip1.max(), mip2.max(), mip3.max())
    vmax = 0.98 * max_obs
    return (np.clip(mip1, 0, vmax) / vmax,
            np.clip(mip2, 0, vmax) / vmax,
            np.clip(mip3, 0, vmax) / vmax)


def to_image(fig):
    fig.subplots_adjust(hspace=0, left=0, right=1, wspace=0)
    fig.canvas.draw()       # draw the canvas, cache the renderer
    image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
    image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return image


def before_after_images(orig_file, aligned_file, model_file, imagenum):
    fig, ax = plt.subplots(ncols=2, figsize=(10, 5))
    fig.subplots_adjust(hspace=0, left=0, right=1, wspace=0)
    for _ax in ax:
        _ax.clear()
    orig_img = nb.load(orig_file).get_fdata()
    aligned_img = nb.load(aligned_file).get_fdata()
    model_img = nb.load(model_file).get_fdata()
    orig_mip, aligned_mip, target_mip = scaled_mip(orig_img, aligned_img, model_img, 0)

    # Get contours for the orig, aligned images
    orig_contours = measure.find_contours(orig_mip, 0.7)
    aligned_contours = measure.find_contours(aligned_mip, 0.7)
    target_contours = measure.find_contours(target_mip, 0.7)

    orig_contours_low = measure.find_contours(orig_mip, 0.05)
    aligned_contours_low = measure.find_contours(aligned_mip, 0.05)
    target_contours_low = measure.find_contours(target_mip, 0.05)

    # Plot before
    ax[0].imshow(orig_mip, vmax=1., vmin=0, origin="lower", cmap="gray",
                 interpolation="nearest")
    ax[1].imshow(target_mip, vmax=1., vmin=0, origin="lower", cmap="gray",
                 interpolation="nearest")
    ax[0].text(1, 1, "%03d: Before" % imagenum, fontsize=16, color='white')
    for contour in target_contours + target_contours_low:
        ax[0].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#e7298a")
        ax[1].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#e7298a")
    for contour in orig_contours + orig_contours_low:
        ax[1].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#d95f02")
        ax[0].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#d95f02")
    for axis in ax:
        axis.set_xticks([])
        axis.set_yticks([])

    before_image = to_image(fig)

    # Plot after
    for _ax in ax:
        _ax.clear()
    ax[0].imshow(aligned_mip, vmax=1., vmin=0, origin="lower", cmap="gray",
                 interpolation="nearest")
    ax[1].imshow(target_mip, vmax=1., vmin=0, origin="lower", cmap="gray",
                 interpolation="nearest")
    ax[0].text(1, 1, "%03d: After" % imagenum, fontsize=16, color='white')
    for contour in target_contours + target_contours_low:
        ax[0].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#e7298a")
        ax[1].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#e7298a")
    for contour in aligned_contours + aligned_contours_low:
        ax[1].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#d95f02")
        ax[0].plot(contour[:, 1], contour[:, 0], linewidth=2, alpha=0.9, color="#d95f02")
    for axis in ax:
        axis.set_xticks([])
        axis.set_yticks([])
    after_image = to_image(fig)

    return before_image, after_image


def _iteration_summary_plot(iters_df, out_file):
    iters = list([item[1] for item in iters_df.groupby('iter_num')])
    shift_cols = ["shiftX", "shiftY", "shiftZ"]
    rotate_cols = ["rotateX", "rotateY", "rotateZ"]
    shifts = np.stack([df[shift_cols] for df in iters], -1)
    rotations = np.stack([df[rotate_cols] for df in iters], -1)

    rot_diffs = np.diff(rotations, axis=2).squeeze()
    shift_diffs = np.diff(shifts, axis=2).squeeze()
    if len(iters) == 2:
        rot_diffs = rot_diffs[..., np.newaxis]
        shift_diffs = shift_diffs[..., np.newaxis]

    shiftdiff_dfs = []
    rotdiff_dfs = []
    for diffnum, (rot_diff, shift_diff) in enumerate(zip(rot_diffs.T, shift_diffs.T)):
        shiftdiff_df = pd.DataFrame(shift_diff.T, columns=shift_cols)
        shiftdiff_df['difference_num'] = "%02d" % diffnum
        shiftdiff_dfs.append(shiftdiff_df)

        rotdiff_df = pd.DataFrame(rot_diff.T, columns=rotate_cols)
        rotdiff_df['difference_num'] = "%02d" % diffnum
        rotdiff_dfs.append(rotdiff_df)

    shift_diffs = pd.concat(shiftdiff_dfs, axis=0)
    rotate_diffs = pd.concat(rotdiff_dfs, axis=0)

    # Plot shifts
    sns.set()
    fig, ax = plt.subplots(ncols=2, figsize=(10, 5))
    sns.violinplot(x="variable", y="value",
                   hue="difference_num",
                   ax=ax[0],
                   data=shift_diffs.melt(id_vars=['difference_num']))
    ax[0].set_ylabel("mm")
    ax[0].set_title("Shift")

    # Plot rotations
    sns.violinplot(x="variable", y="value",
                   hue="difference_num",
                   data=rotate_diffs.melt(id_vars=['difference_num']))
    ax[1].set_ylabel("Degrees")
    ax[1].set_title("Rotation")
    sns.despine(offset=10, trim=True, fig=fig)
    fig.savefig(out_file)
