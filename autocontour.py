import os
import argparse
import SimpleITK as sitk
import numpy as np

from Automasker import Automasker


def autocontour(img):

    # Close any open edges, prevent hollow mask
    depth = img.GetDepth()

    stats_filter = sitk.StatisticsImageFilter()

    thresh_filter = sitk.BinaryThresholdImageFilter()
    thresh_filter.SetLowerThreshold(2)
    thresh_filter.SetUpperThreshold(9999)
    thresh_img = thresh_filter.Execute(img)

    fill_hole_filter = sitk.BinaryFillholeImageFilter()
    fill_hole_filter.SetForegroundValue(1)

    dilate_filter = sitk.BinaryDilateImageFilter()
    dilate_filter.SetForegroundValue(1)
    dilate_filter.SetKernelRadius(5)
    dilate_filter.SetKernelType(sitk.sitkBall)

    erode_filter = sitk.BinaryErodeImageFilter()
    erode_filter.SetForegroundValue(1)
    erode_filter.SetKernelRadius(5)
    erode_filter.SetKernelType(sitk.sitkBall)

    # closed = dilate_filter.Execute(thresh_img)
    # closed = erode_filter.Execute(closed)

    for z in range(depth-1, -1, -1):
        pre_fill = thresh_img[:,:,z]
        pre_fill = dilate_filter.Execute(pre_fill)
        pre_fill = erode_filter.Execute(pre_fill)
        stats_filter.Execute(pre_fill)
        pre_mean = stats_filter.GetMean()

        post_fill = fill_hole_filter.Execute(pre_fill)
        stats_filter.Execute(post_fill)
        post_mean = stats_filter.GetMean()
        # print(post_mean - pre_mean)

        if (post_mean - pre_mean) > 0.025:
            post_fill -= pre_fill
            post_fill = sitk.Cast(post_fill, sitk.sitkFloat32)
            img[:,:,z] += post_fill*5
            break
    
    for z in range(depth):
        pre_fill = thresh_img[:,:,z]
        pre_fill = dilate_filter.Execute(pre_fill)
        pre_fill = erode_filter.Execute(pre_fill)
        stats_filter.Execute(pre_fill)
        pre_mean = stats_filter.GetMean()

        post_fill = fill_hole_filter.Execute(pre_fill)
        stats_filter.Execute(post_fill)
        post_mean = stats_filter.GetMean()
        # print(post_mean - pre_mean)

        if (post_mean - pre_mean) > 0.025:
            post_fill -= pre_fill
            post_fill = sitk.Cast(post_fill, sitk.sitkFloat32)
            img[:,:,z] += post_fill*5
            break
    
    # img = convert_hu_to_bmd(img, mu_water, rescale_slope, rescale_intercept)

    pad_size = [16, 16, 16]
    padded_img = sitk.ConstantPad(img, pad_size, pad_size, 0)

    auto_contour = Automasker()
    prx_mask = auto_contour.get_periosteal_mask(padded_img, 1)
    dst_mask = auto_contour.get_periosteal_mask(padded_img, 2)

    # Step 3: Depad the Masks
    original_size = img.GetSize()
    depad_lower = [16, 16, 16]  # Amount to crop from the lower bounds
    depad_upper = [original_size[i] - 16 for i in range(3)]  # Upper crop to restore original size

    prx_mask = sitk.Crop(prx_mask, depad_lower, depad_lower)
    dst_mask = sitk.Crop(dst_mask, depad_lower, depad_lower)

    # Create a mask for the entire joint
    mask = prx_mask*(1-dst_mask) | (dst_mask*2)
    # mask = prx_mask + dst_mask
    # mask = mask != 0

    return dst_mask, prx_mask, mask


def main():
    # Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=str, help="Image (path + filename)")
    parser.add_argument("out_image_path", type=str, help="Output image path")
    args = parser.parse_args()

    image_path = args.image_path
    out_image_path = args.out_image_path
    # mask_path = args.mask_path

    # Create a new folder to hold the output images
    image_dir = os.path.dirname(image_path)
    basename = os.path.splitext(os.path.basename(image_path))[0]

    prx_mask_path = os.path.join(image_dir, basename + "_PRX_MASK.nii")
    dst_mask_path = os.path.join(image_dir, basename + "_DST_MASK.nii")
    # mask_path = os.path.join(output_dir, basename + "_MASK.nii.gz")

    # Read in images as floats to increase precision
    image = sitk.ReadImage(image_path, sitk.sitkFloat32)
    # mask = sitk.ReadImage(mask_path, sitk.sitkFloat32)

    # dilate_filter = sitk.BinaryDilateImageFilter()
    # dilate_filter.SetForegroundValue(1)
    # dilate_filter.SetKernelRadius(2)
    # dilate_filter.SetKernelType(sitk.sitkBall)
    # # image = sitk.Cast(image, sitk.sitkInt8)
    # dilated_mask = dilate_filter.Execute(mask)

    # transform = sitk.CenteredTransformInitializer(mask, 
    #                                               image, 
    #                                               sitk.VersorTransform((1,0,0), np.pi), 
    #                                               sitk.CenteredTransformInitializerFilter.GEOMETRY)

    # masked_image = sitk.Resample(image, mask, transform, sitk.sitkLinear, 0, image.GetPixelID())
    # image = sitk.Normalize(image)
    # sitk.WriteImage(image, image_path)
    # exit()

    # Run the autocontour method for each bone
    image = sitk.Cast(sitk.Normalize(image), sitk.sitkFloat32)
    dst_mask, prx_mask, mask = autocontour(image)

    sitk.WriteImage(mask, out_image_path)
    # sitk.WriteImage(prx_mask, prx_mask_path)
    # sitk.WriteImage(dst_mask, dst_mask_path)



if __name__ == "__main__":
    main()
