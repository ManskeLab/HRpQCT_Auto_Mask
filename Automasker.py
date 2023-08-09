import SimpleITK as sitk
import time
from scipy import interpolate

# import yaml


class Automasker:


    def get_periosteal_mask(self, img, component):
        """
        Compute the periosteal mask from an input image.

        Parameters
        ----------
        img : sitk.Image
            The gray-scale AIM. Currently this is written for images in HU,
            if you want to input a density image then you'll need to modify
            the lower and upper thresholds to be in the correct units.

        Returns
        -------
        sitk.Image
            A binary image that is the periosteal mask.
        """

        print("Applying Gaussian filter")

        # define dilation and erosion filters
        dilate_filter = sitk.BinaryDilateImageFilter()
        dilate_filter.SetForegroundValue(1)
        dilate_filter.SetKernelRadius(2)
        dilate_filter.SetKernelType(sitk.sitkBall)

        erode_filter = sitk.BinaryErodeImageFilter()
        erode_filter.SetForegroundValue(1)
        erode_filter.SetKernelRadius(2)
        erode_filter.SetKernelType(sitk.sitkBall)

        fillhole_filter = sitk.BinaryFillholeImageFilter()
        fillhole_filter.SetForegroundValue(1)

        # Blur image, TODO try other sitk filters later
        sigma_over_spacing = img.GetSpacing()[0]
        print(sigma_over_spacing)
        gaussian_filter = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian_filter.SetSigma(sigma_over_spacing)
        gaussian_img = gaussian_filter.Execute(img)
        # sitk.WriteImage(gaussian_img, 'Z:/work2/manske/temp/automaskfix/smooth.nii')
        # median_filter = sitk.MedianImageFilter()
        # median_filter.SetRadius(2)
        # median_img = median_filter.Execute(img)
        # sitk.WriteImage(median_img, 'Z:/work2/manske/temp/automaskfix/median.nii')  

        rough_mask = sitk.BinaryThreshold(gaussian_img,
                              lowerThreshold= 1, 
                              upperThreshold= 9999, 
                              insideValue=1)
        
        # rough_mask = dilate_filter.Execute(rough_mask)
        # rough_mask = fillhole_filter.Execute(rough_mask)
        # rough_mask = erode_filter.Execute(rough_mask)
        # sitk.WriteImage(rough_mask, 'Z:/work2/manske/temp/automaskfix/fill.nii') 

        dilate_filter.SetKernelRadius(6)
        erode_filter.SetKernelRadius(6)

        thresh_img2 = rough_mask
        img_conn = sitk.ConnectedComponent(thresh_img2, thresh_img2)
        img_conn = sitk.RelabelComponent(img_conn, sortByObjectSize=True)
        img_segmented = 1 * (img_conn == component)
        # sitk.WriteImage(img_segmented, 'Z:/work2/manske/temp/automaskfix/img_{}.nii'.format(component))

        smoother = sitk.AntiAliasBinaryImageFilter()
        thresh_img2 = smoother.Execute(img_segmented)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/smoother_nonbin.nii')
        thresh_img2 = thresh_img2 != -4
        thresh_img2 = sitk.Cast(thresh_img2, sitk.sitkUInt8)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/smoother_{}.nii'.format(component))

        distance_map_filter = sitk.SignedMaurerDistanceMapImageFilter()
        thresh_img2 = distance_map_filter.Execute(thresh_img2)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/distance_{}.nii'.format(component))

        thresh_img2 = sitk.BinaryThreshold(thresh_img2, 
                              lowerThreshold= -9999, 
                              upperThreshold= 300, 
                              insideValue=1)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/distance_thresh_{}.nii'.format(component))
        
        depth = img.GetDepth()

        stats_filter = sitk.StatisticsImageFilter()

        for z in range(depth-1, -1, -1):
            pre_fill = thresh_img2[:,:,z]
            stats_filter.Execute(pre_fill)
            pre_mean = stats_filter.GetMean()

            post_fill = fillhole_filter.Execute(pre_fill)
            stats_filter.Execute(post_fill)
            post_mean = stats_filter.GetMean()

            if (post_mean - pre_mean) > 0:
                post_fill -= pre_fill
                thresh_img2[:,:,z] += post_fill
                print(z)
                break

        for z in range(depth):
            pre_fill = thresh_img2[:,:,z]
            stats_filter.Execute(pre_fill)
            pre_mean = stats_filter.GetMean()

            post_fill = fillhole_filter.Execute(pre_fill)
            stats_filter.Execute(post_fill)
            post_mean = stats_filter.GetMean()

            if (post_mean - pre_mean) > 0:
                post_fill -= pre_fill
                thresh_img2[:,:,z] += post_fill
                print(z)
                break
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/prefilled_{}.nii'.format(component))        
        thresh_img2 = fillhole_filter.Execute(thresh_img2)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/filled_{}.nii'.format(component))

        erode_filter.SetKernelRadius(21)
        thresh_img2 = erode_filter.Execute(thresh_img2)
        # sitk.WriteImage(thresh_img2, 'Z:/work2/manske/temp/automaskfix/filled_eroded_{}.nii'.format(component))

        print("Ready!!")

        return thresh_img2