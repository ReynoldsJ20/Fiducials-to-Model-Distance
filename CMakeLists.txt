cmake_minimum_required(VERSION 3.13.4)

project(FiducialToModelDistance)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/ReynoldsJ20/SlicerFiducialsToModelDistance")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Jesse Reynolds (Canterbury District Health Board) with assistance from Andras Lasso (Queen's University)")
set(EXTENSION_DESCRIPTION "This module computes the distances between a set of fiducial points and either the surface of a model, or another set of fiducial points. The results are displayed in two tables.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/ReynoldsJ20/SlicerFiducialsToModelDistance/master/FiducialtoModelDistance.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/ReynoldsJ20/SlicerFiducialsToModelDistance/master/Screenshots/ScreenShot1.PNG https://raw.githubusercontent.com/ReynoldsJ20/SlicerFiducialsToModelDistance/master/Screenshots/ScreenShot2.PNG")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(FiducialtoModelDistance)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
