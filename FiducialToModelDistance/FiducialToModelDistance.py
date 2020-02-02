import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from decimal import Decimal

#
# FiducialToModelDistance
#

class FiducialToModelDistance(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Fiducial to Model Distance"
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = []
    self.parent.contributors = ["Jesse Reynolds (Canterbury District Health Board) with assistance from Andras Lasso (Queen's University), "] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module computes the distances between a set of fiducial points and a surface model. The results are displayed in a table.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Andras Lasso (Queen's University) and Jesse Reynolds (Canterbury District Health Board)."""

#
# FiducialToModelDistanceWidget
#

class FiducialToModelDistanceWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/FiducialToModelDistance.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    self.ui.fiducialToModelInputModelSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.fiducialToModelInputFiducialSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.fiducialToFiducialInputMovingFiducialSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.fiducialToFiducialInputFixedFiducialSelector.setMRMLScene(slicer.mrmlScene)

    # connections
    self.ui.fiducalToModelApplyButton.connect('clicked(bool)', self.onFiducalToModelApplyButton)
    self.ui.showPointsTableButton.connect('clicked(bool)', self.onShowPointsFromSurfaceDistanceTableButton)
    self.ui.showErrorMetricTableButton.connect('clicked(bool)', self.onFiducialToModelShowErrorMetricTableButton)
    self.ui.fiducialToModelInputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.fiducialToModelInputFiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.fiducialToFiducialInputMovingFiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectFiducialtoFiducial)
    self.ui.fiducialToFiducialInputFixedFiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectFiducialtoFiducial)
    self.ui.fiducialToFiducialApplyButton.connect('clicked(bool)', self.onFiducialToFiducialApplyButton)
    self.ui.fiducialToFiducialShowPointsButton.connect('clicked(bool)', self.onShowClosestPointToPointDistanceTableButton)
    self.ui.fiducialToFiducialShowErrorMetricTableButton.connect('clicked(bool)', self.onFiducialToFiducialShowErrorMetricTable)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.ui.fiducalToModelApplyButton.enabled = self.ui.fiducialToModelInputModelSelector.currentNode() and self.ui.fiducialToModelInputFiducialSelector.currentNode()
    
  def onSelectFiducialtoFiducial(self):
    self.ui.fiducialToFiducialApplyButton.enabled = self.ui.fiducialToFiducialInputMovingFiducialSelector.currentNode() and self.ui.fiducialToFiducialInputFixedFiducialSelector.currentNode()

  def onFiducalToModelApplyButton(self):
    logic = FiducialToModelDistanceLogic()
    logic.runFiducialToModel(self.ui.fiducialToModelInputModelSelector.currentNode(), self.ui.fiducialToModelInputFiducialSelector.currentNode())
    
    self.ui.showPointsTableButton.enabled = True
    self.ui.showErrorMetricTableButton.enabled = True
    
  def onShowPointsFromSurfaceDistanceTableButton(self):
    logic = FiducialToModelDistanceLogic()
    logic.pointsTableButton()
    
  def onFiducialToModelShowErrorMetricTableButton(self):
    logic = FiducialToModelDistanceLogic()
    logic.errorTableButton()
    
  def onFiducialToFiducialApplyButton(self):
    logic = FiducialToModelDistanceLogic()
    logic.runFiducialToFiducial(self.ui.fiducialToFiducialInputFixedFiducialSelector.currentNode(), self.ui.fiducialToFiducialInputMovingFiducialSelector.currentNode())
    
    self.ui.fiducialToFiducialShowPointsButton.enabled = True
    self.ui.fiducialToFiducialShowErrorMetricTableButton.enabled = True
    
  def onShowClosestPointToPointDistanceTableButton(self):
    logic = FiducialToModelDistanceLogic()
    logic.fiducialPointsTableButton()
    
  def onFiducialToFiducialShowErrorMetricTable(self):
    logic = FiducialToModelDistanceLogic()
    logic.fiducialErrorTableButton()
  

#
# FiducialToModelDistanceLogic
#

class FiducialToModelDistanceLogic(ScriptedLoadableModuleLogic):

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

  def isValidInputData(self, input1, input2):
   
    # Validates if the output is not the same as input
    if not input1:
      logging.debug('isValidInputData failed: no input model node defined')
      return False
    if not input2:
      logging.debug('isValidInputData failed: no input fiducial node defined')
      return False
    if input1.GetID() == input2.GetID():
      logging.debug('isValidInputOutputData failed: input and output are the same.')
      return False
    return True

  def runFiducialToModel(self, inputModel, inputFiducials):
    
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
    meanOfAbsCol = vtk.vtkDoubleArray()
    meanOfAbsCol.SetName("Mean of Absolute Values")
    rmsCol = vtk.vtkDoubleArray()
    rmsCol.SetName("Root Mean Square")
    maxCol = vtk.vtkDoubleArray()
    maxCol.SetName("Maximum Absolute Distance")
    minCol = vtk.vtkDoubleArray()
    minCol.SetName("Minimum Absolute Distance")

    distanceFilter = vtk.vtkImplicitPolyDataDistance()
    distanceFilter.SetInput(surface_World);
    nOfFiducialPoints = inputFiducials.GetNumberOfFiducials()
    totalabsDistance = 0
    totalsquareDistance = 0
    for i in range(0, nOfFiducialPoints):
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
      
    # Store minimum and maximum absolute values
    maxCol.InsertNextValue(maxVal)
    minCol.InsertNextValue(minVal)
    
    # Calculate and store Mean of Absolute Values
    meanOfAbs = totalabsDistance / nOfFiducialPoints
    meanOfAbsCol.InsertNextValue(meanOfAbs)
    
    # Calculate and store RMS
    rms = (totalsquareDistance / nOfFiducialPoints) ** 0.5
    rmsCol.InsertNextValue(rms)

    # Create a table from result arrays
    resultTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Points from surface distance")
    resultTableNode.AddColumn(indexCol)
    resultTableNode.AddColumn(labelCol)
    resultTableNode.AddColumn(distanceCol)
    
    # Create a table for Error Metrics
    errorMetricTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Fiducial To Model Error Metrics Table")
    errorMetricTableNode.AddColumn(meanOfAbsCol)
    errorMetricTableNode.AddColumn(rmsCol)
    errorMetricTableNode.AddColumn(maxCol)
    errorMetricTableNode.AddColumn(minCol)

    # Show table in view layout
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(errorMetricTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()

    logging.info('Processing completed')

    return True
  
  def pointsTableButton(self):
  
    try:
      resultTableNode = slicer.util.getNode('Points from surface distance')
    except:
      slicer.util.errorDisplay('There is no table named "Points from Surface Distance Table"')
      return False
  
    # Show table in view layout
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(resultTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
    
    return True
    
  def errorTableButton(self):
  
    try:
      errorMetricTableNode = slicer.util.getNode('Fiducial To Model Error Metrics Table')
    except:
      slicer.util.errorDisplay('There is no table named "Fiducial To Model Error Metrics Table"')
      return False
  
    # Show table in view layout
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(errorMetricTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
    
    return True
    
  def runFiducialToFiducial(self, inputFixedFiducials, inputMovingFiducials):
  
    if not self.hasFiducialData(inputFixedFiducials):
      slicer.util.errorDisplay('Invalid Fixed Input Fiducials - Check Error Log For Details')
      return False
      
    if not self.hasFiducialData(inputMovingFiducials):
      slicer.util.errorDisplay('Invalid Input Moving Fiducials - Check Error Log For Details')
      return False
      
    if not self.isValidInputData(inputFixedFiducials, inputMovingFiducials):
      slicer.util.errorDisplay('Invalid Inputs Defined - Check Error Log For Details')
      return False
    
    # Create arrays to store data
    indexCol = vtk.vtkIntArray()
    indexCol.SetName("Index")
    labelCol = vtk.vtkStringArray()
    labelCol.SetName("Name")
    distanceCol = vtk.vtkDoubleArray()
    distanceCol.SetName("Distance")
    meanCol = vtk.vtkDoubleArray()
    meanCol.SetName("Mean Distance")
    rmsCol = vtk.vtkDoubleArray()
    rmsCol.SetName("Root Mean Square")
    maxCol = vtk.vtkDoubleArray()
    maxCol.SetName("Maximum Distance")
    minCol = vtk.vtkDoubleArray()
    minCol.SetName("Minimum Distance")
    hausdorffCol = vtk.vtkDoubleArray()
    hausdorffCol.SetName("Hausdorff Distance")
    
    # Calculate closest point to point distance
    nOfMovingFiducialPoints = inputMovingFiducials.GetNumberOfFiducials()
    nOfFixedFiducialPoints = inputFixedFiducials.GetNumberOfFiducials()
    totalDistance = 0
    totalSquareDistance = 0
    for i in range(0, nOfMovingFiducialPoints):
      movingPointWorld = [0,0,0]
      inputMovingFiducials.GetNthControlPointPositionWorld(i, movingPointWorld)
      for j in range(0, nOfFixedFiducialPoints):
        fixedPointWorld = [0,0,0]
        inputFixedFiducials.GetNthControlPointPositionWorld(j, fixedPointWorld)
        dist = (vtk.vtkMath.Distance2BetweenPoints(movingPointWorld,fixedPointWorld)) ** 0.5
        if j == 0:
          minDist = dist
          closestLabel = inputFixedFiducials.GetNthControlPointLabel(j)
        elif minDist > dist:
          minDist = dist
          closestLabel = inputFixedFiducials.GetNthControlPointLabel(j)
      indexCol.InsertNextValue(i)
      labelCol.InsertNextValue(inputMovingFiducials.GetNthControlPointLabel(i) + " to " + closestLabel)
      distanceCol.InsertNextValue(minDist)
      if i == 0:
        maxMinDist = minDist
        minMinDist = minDist
      elif minMinDist > minDist:
        minMinDist = minDist
      elif maxMinDist < minDist:
        maxMinDist = minDist
      totalDistance += minDist
      totalSquareDistance += minDist ** 2
      
    # Calculate min p2p distance from fixed to moving fiducials for Hausdorff distance
    for i in range(0, nOfFixedFiducialPoints):
      fixedPointWorld = [0,0,0]
      inputFixedFiducials.GetNthControlPointPositionWorld(i, fixedPointWorld)
      for j in range(0, nOfMovingFiducialPoints):
        movingPointWorld = [0, 0, 0]
        inputMovingFiducials.GetNthControlPointPositionWorld(j, movingPointWorld)
        dist = (vtk.vtkMath.Distance2BetweenPoints(movingPointWorld,fixedPointWorld)) ** 0.5
        if j == 0:
          minDist2 = dist
        elif minDist2 > dist:
          minDist2 = dist
      if i == 0:
        minMinDist2 = minDist2
      elif minMinDist2 > minDist2:
        minMinDist2 = minDist2
    
    # Hausdorff Distance is the max of the minimum distances
    if minMinDist2 > minMinDist:
      hausdorffDist = minMinDist2
    else:
      hausdorffDist = minMinDist
    hausdorffCol.InsertNextValue(hausdorffDist)
      
    # Store min and max
    maxCol.InsertNextValue(maxMinDist)
    minCol.InsertNextValue(minMinDist)
    
    # Calculate and store mean and rms
    mean = totalDistance / nOfMovingFiducialPoints
    meanCol.InsertNextValue(mean)
    rms = (totalSquareDistance / nOfMovingFiducialPoints) ** 0.5
    rmsCol.InsertNextValue(rms)
      
    # Create a table from result arrays
    resultTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Minimum Point to Point Distance")
    resultTableNode.AddColumn(indexCol)
    resultTableNode.AddColumn(labelCol)
    resultTableNode.AddColumn(distanceCol)
    
    # Create error metric table
    errorMetricTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Fiducial to Fiducial Error Metrics Table")
    errorMetricTableNode.AddColumn(meanCol)
    errorMetricTableNode.AddColumn(rmsCol)
    errorMetricTableNode.AddColumn(maxCol)
    errorMetricTableNode.AddColumn(minCol)
    errorMetricTableNode.AddColumn(hausdorffCol)
    
    # Show table in view layout
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(errorMetricTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
      
  def fiducialPointsTableButton(self):
  
    try:
      resultTableNode = slicer.util.getNode('Minimum Point to Point Distance')
    except:
      slicer.util.errorDisplay('There is no table named "Minimum Point to Point Distance"')
      return False
  
    # Show table in view layout
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(resultTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
    
    return True
    
  def fiducialErrorTableButton(self):
  
    try:
      errorMetricTableNode = slicer.util.getNode('Fiducial to Fiducial Error Metrics Table')
    except:
      slicer.util.errorDisplay('There is no table named "Fiducial to Fiducial Error Metrics Table"')
      return False
  
    # Show table in view layout
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(errorMetricTableNode.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
    
    return True
        
          
  


class FiducialToModelDistanceTest(ScriptedLoadableModuleTest):
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
    self.test_FiducialToModelDistance1()

  def test_FiducialToModelDistance1(self):

    self.delayDisplay("Starting the test")
    
    # Create a 100 x 100 x 100mm cube
    cube = vtk.vtkCubeSource()
    cube.SetBounds(-50, 50, -50, 50, -50, 50)
    cube.Update()
    modelsLogic = slicer.modules.models.logic()
    modelsLogic.AddModel(cube.GetOutput())
    modelNode = slicer.util.getNode("Model")
    modelNode.GetDisplayNode().SetSliceIntersectionVisibility(1)
    
    # function for adding fiducial points
    def addFiducialPoints(title, fiducialPoints):
      fiducialNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', title)
      point = vtk.vtkVector3d()
      for fiducialPoint in fiducialPoints:
        point.Set(fiducialPoint[0], fiducialPoint[1], fiducialPoint[2])
        fiducialNode.AddControlPointWorld(point)
        
    # Add a set of moving fiducial points and a set of fixed fiducial points
    movingFiducialPoints = [[51, 0, 0], [-52, 0, 0], [0, 51, 0], [0, -52, 0], [0, 0, 51], [0, 0, -52]]
    fixedFiducialPoints = [[50, 0, 0], [-50, 0, 0], [0, 50, 0], [0, -50, 0], [0, 0, 50], [0, 0, -50]]
    
    addFiducialPoints("Moving", movingFiducialPoints)
    addFiducialPoints("Fixed", fixedFiducialPoints)
    
    # Change color of moving fiducial node to blue
    fixedFiducialNode = slicer.util.getNode('Fixed')
    movingFiducialNode = slicer.util.getNode('Moving')
    displayNode = movingFiducialNode.GetDisplayNode()
    displayNode.SetSelectedColor(0,0,1)
    
    # Some display settings
    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()
    
    # Run Fiducial to Model Distance
    moduleWidget = slicer.modules.FiducialToModelDistanceWidget
    moduleWidget.ui.fiducialToModelInputFiducialSelector.setCurrentNode(movingFiducialNode)
    moduleWidget.ui.fiducialToModelInputModelSelector.setCurrentNode(modelNode)
    moduleWidget.onFiducalToModelApplyButton()
    moduleWidget.onShowPointsFromSurfaceDistanceTableButton()
    moduleWidget.onFiducialToModelShowErrorMetricTableButton()
    self.delayDisplay('Fiducial to Model Distance Test Passed!')
    
    # Run Fiducial to Fiducial Distance
    moduleWidget.ui.fiducialToFiducialInputMovingFiducialSelector.setCurrentNode(movingFiducialNode)
    moduleWidget.ui.fiducialToFiducialInputFixedFiducialSelector.setCurrentNode(fixedFiducialNode)
    moduleWidget.onFiducialToFiducialApplyButton()
    moduleWidget.onShowClosestPointToPointDistanceTableButton()
    moduleWidget.onFiducialToFiducialShowErrorMetricTable()
    self.delayDisplay('Fiducial to Fiducial Distance Test Passed!')
    
    
    self.delayDisplay("Test passed!")
    
    logging.info("""Mean Distances should be 1.5mm
Root Mean Square should be 1.581mm
Maximum Distance should be 2mm
Minimum Distance should be 1mm
Hausdorff Distance should be 1mm""")
    
    slicer.util.messageBox("""See Python Interactor for Correct Error Metric Values 
Compare These Values Against the Values in the Tables""")
