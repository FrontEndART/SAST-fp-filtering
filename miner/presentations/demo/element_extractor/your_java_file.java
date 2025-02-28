public class ExampleJavaFile {

    public static void main(String[] args) {
        int result = addNumbers(5, 7);
        System.out.println("The result is: " + result);
    }

    public static int addNumbers(int a, int b) {
        return a + b;
    }

    public void someOtherMethod() {
        // This is another method
    }

    private static double calculateArea(double radius) {
        return Math.PI * radius * radius;
    }
}
