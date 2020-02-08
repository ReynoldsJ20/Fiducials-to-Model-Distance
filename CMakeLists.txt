cmake_minimum_required(VERSION 3.13.4)

project(FiducialtoModelDistance)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/ReynoldsJ20/SlicerFiducialsToModelDistance")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Jesse Reynolds (Canterbury District Health Board) with assistance from Andras Lasso (Queen's University)")
set(EXTENSION_DESCRIPTION "This module computes the distances between a set of fiducial points and either the surface of a model, or another set of fiducial points. The results are displayed in a table.")
set(EXTENSION_ICONURL "https://github.com/ReynoldsJ20/SlicerFiducialsToModelDistance/blob/master/FiducialtoModelDistance.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/ReynoldsJ20/SlicerFiducialsToModelDistance/tree/master/Screenshots")
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
