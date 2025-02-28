package my_app;

public class Main{
	public static final int POPULATION = 0;
	
	
	public static void main(String[] args) {
		Employee p = new Employee();
		String[] hobby = new String[]{"tailer"};
		p.setHobbies(hobby);
		Date personDate = p.getBirthDate();
		p.setBirthDate(personDate);
		System.out.println(p.getHobbies()[0] + p.getBirthDate().toString());
	}
}
