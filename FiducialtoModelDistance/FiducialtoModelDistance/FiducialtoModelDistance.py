import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from decimal import Decimal

#
# FiducialtoModelDistance
#

class FiducialtoModelDistance(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Fiducial to Model Distance"
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = []
    self.parent.contributors = ["Andras Lasso (Queen's University), Jesse Reynolds (Canterbury District Health Board)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module computes the distances between a set of fiducial points and a surface model. The results are displayed in a table.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Andras Lasso (Queen's University) and Jesse Reynolds (Canterbury District Health Board)."""

#
# FiducialtoModelDistanceWidget
#

class FiducialtoModelDistanceWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/FiducialtoModelDistance.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    self.ui.inputModelSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.inputFiducialSelector.setMRMLScene(slicer.mrmlScene)

    # connections
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.inputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.inputFiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.ui.applyButton.enabled = self.ui.inputModelSelector.currentNode() and self.ui.inputFiducialSelector.currentNode()

  def onApplyButton(self):
    logic = FiducialtoModelDistanceLogic()
    runOutput = logic.run(self.ui.inputModelSelector.currentNode(), self.ui.inputFiducialSelector.currentNode())
    
    # set text in output boxes using various outputs of the run method
    self.ui.absMeanBox.setText(runOutput[1])
    self.ui.rmsBox.setText(runOutput[2])
    self.ui.absMax.setText(runOutput[3])
    self.ui.absMin.setText(runOutput[4])

#
# FiducialtoModelDistanceLogic
#

class FiducialtoModelDistanceLogic(ScriptedLoadableModuleLogic):

  def hasModelData(self,inputModel):
    
    if not inputModel:
      logging.debug('hasModelData failed: no model node')
      return False
    if inputModel.GetPolyData() is None:
      logging.debug('hasModelData failed: no model data in model node')
      return False
    return True
    
  def hasFiducialData(self,inputFiducials):
    
    # Checks if input fiducial data is valid
    if not inputFiducials:
      logging.debug('hasFiducialData failed: no fiducial node')
      return False
    if inputFiducials.GetNumberOfFiducials() == 0:
      logging.debug('hasFiducialData failed: no fiducial data in fiducial node')
      return False
    return True

  def isValidInputData(self, inputModel, inputFiducials):
   
    # Validates if the output is not the same as input
    if not inputModel:
      logging.debug('isValidInputData failed: no input model node defined')
      return False
    if not inputFiducials:
      logging.debug('isValidInputData failed: no input fiducial node defined')
      return False
    return True

  def run(self, inputModel, inputFiducials):
    """
    Run the actual algorithm
    """
    
    if not self.hasFiducialData(inputFiducials):
      slicer.util.errorDisplay('Invalid Input Fiducials - Check Error Log For Details')
      return False
      
    if not self.hasModelData(inputModel):
      slicer.util.errorDisplay('Invalid Input Model - Check Error Log For Details')
      return False
      
    if not self.isValidInputData(inputModel, inputFiducials):
      slicer.util.errorDisplay('Invalid Inputs Defined - Check Error Log For Details')
      return False
    
    logging.info('Processing started')

    # Transform model polydata to world coordinate system
    if inputModel.GetParentTransformNode():
      transformModelToWorld = vtk.vtkGeneralTransform()
      slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(inputModel.GetParentTransformNode(), None, transformModelToWorld)
      polyTransformToWorld = vtk.vtkTransformPolyDataFilter()
      polyTransformToWorld.SetTransform(transformModelToWorld)
      polyTransformToWorld.SetInputData(inputModel.GetPolyData())
      polyTransformToWorld.Update()
      surface_World = polyTransformToWorld.GetOutput()
    else:
      surface_World = inputModel.GetPolyData()

    # Create arrays to store results
    indexCol = vtk.vtkIntArray()
    indexCol.SetName("Index")
    labelCol = vtk.vtkStringArray()
    labelCol.SetName("Name")
    distanceCol = vtk.vtkDoubleArray()
    distanceCol.SetName("Distance")

    distanceFilter = vtk.vtkImplicitPolyDataDistance()
    distanceFilter.SetInput(surface_World);
    nOfFiduciallPoints = inputFiducials.GetNumberOfFiducials()
    totalabsDistance = 0
    totalsquareDistance = 0
    for i in range(0, nOfFiduciallPoints):
      point_World = [0,0,0]
      inputFiducials.GetNthControlPointPositionWorld(i, point_World)
      closestPointOnSurface_World = [0,0,0]
      closestPointDistance = distanceFilter.EvaluateFunctionAndGetClosestPoint(point_World, closestPointOnSurface_World)
      indexCol.InsertNextValue(i)
      labelCol.InsertNextValue(inputFiducials.GetNthControlPointLabel(i))
      distanceCol.InsertNextValue(closestPointDistance)
      totalabsDistance += abs(closestPointDistance)   # sum distance absolute values to calculate absolute mean
      totalsquareDistance += closestPointDistance ** 2    # sum squares of distance to calculate root mean square error
      # find the minimum and maximum distance values
      if i == 0:
        minVal = abs(closestPointDistance)
        maxVal = abs(closestPointDistance)
      elif abs(closestPointDistance) > maxVal:
        maxVal = abs(closestPointDistance)
      elif abs(closestPointDistance) < minVal:
        minVal = abs(closestPointDistance)
      
    absMean = totalabsDistance / nOfFiduciallPoints # calculate absolute mean
    rms = (totalsquareDistance / nOfFiduciallPoints) ** 0.5 # calculate root mean square
    
    # set format in the output text boxes. Display values to 3 d.p. and if values are less than 0.001 display as scientific notation
    if absMean < 0.001:
      absMean = '%.3E' % Decimal(absMean)
    else:
      absMean = '%.3f' % absMean
    if rms < 0.001:
      rms = '%.3E' % Decimal(rms)
    else:
      rms = '%.3f' % rms
    if minVal < 0.001:
      minVal = '%.3E' % Decimal(minVal)
    else:
      minVal = '%.3f' % minVal
    if maxVal < 0.001:
      maxVal = '%.3E' % Decimal(maxVal)
    else:
      maxVal = '%.3f' % maxVal

    # Create a table from result arrays
    resultTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Points from surface distance")
    resultTableNode.AddColumn(indexCol)
    resultTableNode.AddColumn(labelCol)
    resultTableNode.AddColumn(distanceCol)

    # Show table in view layout
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(resultTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()

    logging.info('Processing completed')

    return True, absMean, rms, maxVal, minVal # output values to put into the text boxes


class FiducialtoModelDistanceTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_FiducialtoModelDistance1()

  def test_FiducialtoModelDistance1(self):

    self.delayDisplay("Starting the test")
    #
    self.delayDisplay('Test passed!')
